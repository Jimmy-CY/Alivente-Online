# -*- coding: utf-8 -*-
"""test_lease_sign.py - round ES-4, 24 Oct 2026.

THE PAGE A LEASE IS ACTUALLY SIGNED ON, DRIVEN END TO END.

SECTION 3 IS THE ROUND AND IT RUNS THE WHOLE FLOW through Django's
test client, over a real envelope with a real PDF: the house signs,
the tenants are emailed, a tenant signs, the envelope seals and the
copy goes out. Reading the view would prove that the code says those
things. Running it is the only way to find out that it does them in
an order that works.

    A DRY RUN IS NOT A RUN - SB-2, 23 October. That round dry-ran
    clean, passed every gate, and had never once been executed with
    itself applied. Both of its faults were found the first time its
    suite actually ran.

SECTION 4 IS THE LOCK, AND IT IS ASKED THE WAY AN ATTACKER WOULD ASK
IT. The Sign button is disabled until the last page has been on
screen; a disabled button is a courtesy to somebody using the page
and not a check, so the suite posts without the flag and requires a
refusal. His decision of 24 October was the lock AND the notice, so
section 1 requires the notice too.

SECTION 5 IS WHAT MUST NOT LEAK. A seven-day link to a contract that
survives its own expiry is the failure this round is most able to
ship: the page images go back through the token check, the closed
page carries no document, and both are asked rather than asserted.

SECTION 7 EARNS THE STANDALONE DECISION. Four public templates cannot
extend base.html, which puts them outside every colour census in the
tree - test_amber, test_brights, the four test_colour_* suites,
test_cssrules_outside and test_dead_weight all skip standalone pages.
So this suite takes that job and compares all twenty-three copied
token values against base.html itself.

WHAT IS NOT PROVED HERE. That an email actually leaves the building.
The backend is swapped for the in-memory one, because a suite that
sent real mail would send it to whatever address was in the fixture,
from Demetri's own account, every time anybody ran the sweep. What is
proved is what the application handed the mail layer.
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

SUFFIX = '.bak_leasesign'
ME = 'test_lease_sign.py'
PATCHER = 'apply_lease_sign.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-4, 24 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'lease_signing_sign.py')
SIGN = os.path.join(ROOT, 'pages', 'templates', 'lease_sign.html')
DONE = os.path.join(ROOT, 'pages', 'templates', 'lease_sign_done.html')
CLOSED = os.path.join(ROOT, 'pages', 'templates', 'lease_sign_closed.html')
STYLES = os.path.join(ROOT, 'pages', 'templates', 'lease_sign_styles.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
MIDDLEWARE = os.path.join(ROOT, 'pages', 'middleware.py')
VINIT = os.path.join(ROOT, 'pages', 'views', '__init__.py')
GATE = os.path.join(ROOT, PS1)

# THE FILES THIS ROUND EDITED - the only ones with a backup to control
# against. The five it ships were invented, so there is nothing they
# were before.
EDITED = (URLS, VINIT, MIDDLEWARE)
SHIPPED = (VIEW, SIGN, DONE, CLOSED, STYLES)

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
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in EDITED + SHIPPED)
OLD = dict((p, was(p)) for p in EDITED)


def claims(d):
    code = T.python_code_only(d.get(VIEW, ''), payloads=True)
    u = T.python_code_only(d[URLS], payloads=True)
    page = T.code_only_js(d.get(SIGN, ''))
    closed = T.code_only_js(d.get(CLOSED, ''))
    return {
        'a lease can be opened by LINK, with no account':
            "name='lease_sign'" in u and 'def lease_sign(' in code
            and '@login_required' not in code[
                max(0, code.find('def lease_sign(') - 200):
                code.find('def lease_sign(')],
        '  and by SESSION, for the named Alivente signer':
            "name='lease_sign_session'" in u
            and 'def lease_sign_session(' in code,
        '  which is ONE page reached two ways, not two pages':
            code.count('def _sign_view(') == 1
            and code.count("render(request, 'lease_sign.html'") >= 1,
        'the token is matched by HASH and never by value':
            'token_hash=LeaseSigningParty.hash_token' in code,
        'the page says the agreement must be read to the end':
            'read the whole agreement' in page.lower(),
        '  the control says what is still outstanding':
            'ls-why' in page,
        '  and the SERVER refuses a signature without it':
            "request.POST.get('read_to_end')" in code,
        'a signature may be drawn or typed, and the trail keeps them apart':
            'KIND_DRAWN' in code and 'KIND_TYPED' in code,
        'a link holder and a signed-in user are recorded differently':
            'AUTH_SESSION' in code and 'AUTH_TOKEN' in code,
        'the house signature is what SENDS it to the tenants':
            '_invite(' in code and 'LeaseSigning.SENT' in code,
        'the last signature seals and emails the copy':
            'lease_sealing.seal(' in code and '_signed_copy(' in code,
        'the document is served through the token check':
            "name='lease_sign_page'" in u and 'def lease_sign_page(' in code,
        '  and never from a media URL':
            # bool(page) FIRST, AND THAT IS THE WHOLE POINT. The
            # control feeds this an EMPTY page, and `MEDIA_URL not in
            # ''` is true - so without this the claim would hold
            # before the round and the control would report a round
            # that changed nothing. Same shape as the 23 October
            # finding: a claim that passes because the thing is
            # ABSENT is worse than one that fails.
            bool(page) and 'MEDIA_URL' not in page
            and '.original_pdf.url' not in page,
        'the public route is exempt from the module middleware':
            # WITHOUT THIS THE ROUND DOES NOTHING. A1 wrote the same
            # sentence into that file for the emailed password link,
            # and this round rediscovered it the same way: by driving
            # the flow, not by reading it.
            "'sign/'" in T.python_code_only(
                d[MIDDLEWARE], payloads=True).split('LOGIN_ONLY')[0],
        '  and the staff screens under lease-signing/ are not':
            # PAIRED WITH THE CLAIM ABOVE, deliberately. On its own
            # this is true of a file that exempts nothing at all, and
            # a claim that passes because the thing is ABSENT is worse
            # than one that fails - the control would have reported it
            # as holding before the round.
            "'sign/'" in T.python_code_only(
                d[MIDDLEWARE], payloads=True).split('LOGIN_ONLY')[0]
            and "'lease-signing/'" not in T.python_code_only(
                d[MIDDLEWARE], payloads=True).split('LOGIN_ONLY')[0],
        'after the date there is a plain page and no document':
            bool(closed) and 'ls-page' not in closed
            and '<form' not in closed,
        '  which says WHY, rather than being a silent 404':
            'signing period' in closed.lower(),
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)
ok(MARK in NOW[URLS], 'the round dates itself, on one line')

# EVERY ROUTED VIEW IS EXPORTED. RV-1's lesson, and the third module in
# this family to carry the check.
vcode = T.python_code_only(NOW[VIEW], payloads=True)
for name in ('lease_sign', 'lease_sign_page', 'lease_sign_session',
             'lease_sign_page_session'):
    ok(("'%s'" % name) in vcode or ('"%s"' % name) in vcode,
       '%s is in __all__, so the URLconf can see it' % name)


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
before = dict(OLD)
before[VIEW] = ''
before[SIGN] = ''
before[DONE] = ''
before[CLOSED] = ''
before[STYLES] = ''
held = [m for m, v in claims(before).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)
# THE ROUTE NAME, NOT THE SUBSTRING. `lease_signing_list` contains
# the characters 'lease_sign', so a bare `in` check reported that the
# old urls.py already knew how to sign - which it did not. The first
# draft of this control failed for exactly that reason.
ok("name='lease_sign'" not in T.python_code_only(OLD[URLS], payloads=True),
   'CONTROL: there really was no way to sign anything')
ok('lease_signing_sign' not in OLD[VINIT],
   'CONTROL: and the module was not wired in')
ok("'sign/'" not in T.python_code_only(OLD[MIDDLEWARE], payloads=True)
   .split('LOGIN_ONLY')[0],
   'CONTROL: and an anonymous tenant following a link was bounced to a '
   'login page they have no account for - which is exactly what A1 '
   'found with the emailed password link, and is why that file already '
   'carries the sentence')
for p in SHIPPED:
    ok(not os.path.isfile(p + SUFFIX),
       'CONTROL: %s has no backup, because this round INVENTED it - a '
       'backup beside it would mean somebody had been here before'
       % os.path.basename(p))


# ==========================================================================
head('3. DRIVEN - the whole flow, through the client')
# ==========================================================================
#
# A DRY RUN IS NOT A RUN. Reading the view proves the code SAYS these
# things; running it is the only way to find out whether it does them
# in an order that works.
django_up = False
try:
    import datetime as dt
    import shutil
    import tempfile

    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.contrib.auth.models import User
    from django.core import mail
    from django.db import transaction
    from django.test import Client
    from django.test.utils import override_settings
    from django.utils import timezone
    import pages.models as M
    from pages.services import lease_sealing
    django_up = True
except Exception as e:
    skip('sections 3 to 6', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


def a_pdf(pages=2):
    """A real two-page lease, because render_pages opens a real one."""
    import pymupdf
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 110), 'LEASE AGREEMENT', fontsize=18)
        page.insert_text((72, 150), 'Page %d of %d' % (i + 1, pages),
                         fontsize=11)
    raw = doc.tobytes()
    doc.close()
    return raw


class Rollback(Exception):
    """Nothing this suite writes survives it."""


if not django_up:
    skip('the flow', 'no Django')
else:
    from django.core.files.base import ContentFile

    # IS THERE A DATABASE AT ALL? This project is MySQL and the
    # connection details come from the environment, so a tree checked
    # out without them has none. That is a legitimate way to run a
    # sweep - alv_tree.roots() makes the same allowance - and a suite
    # that died of it would turn a missing environment variable into
    # a failing round.
    #
    # ASKED, NOT ASSUMED, and asked where it can be answered: the
    # driver raises AttributeError rather than anything you could
    # catch by name.
    try:
        from django.db import connection
        connection.ensure_connection()
        have_db = True
    except Exception as _e:                            # noqa: BLE001
        have_db = False
        skip('sections 3 to 7, the whole driven flow',
             'no database: %s' % str(_e).split('\n')[0][:70])

    tmp = tempfile.mkdtemp(prefix='alv_es4_')
    # THE MAIL BACKEND IS SWAPPED, and that is not a convenience. A
    # suite that sent real mail would send it from Demetri's own
    # account to whatever address was in the fixture, every time
    # anybody ran the sweep.
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        if not have_db:
            raise Rollback
        with transaction.atomic():
            prop = M.props.objects.create(prop_name='Flat 7, Palikaridi',
                                          prop_country='Cyprus')
            ten = M.tenant.objects.create(
                prop=prop, tenant_type='Individual',
                tenant_name='Mr. Dorian Tirouard',
                tenant_contact_number='+33 661338231',
                tenant_email='dorian.tirouard@example.com',
                tenant_2_name='Mr. Antoine Madelbos',
                tenant_2_email='antoine.madelbos@example.com',
                tenant_lease_start_date=dt.date(2026, 9, 1),
                tenant_lease_end_date=dt.date(2028, 8, 31),
                tenant_current='Yes')

            user = User.objects.create_user(
                username='es4signer', password='not-a-real-password',
                email='signer@example.com', first_name='Demetri',
                last_name='Manias')

            env = M.LeaseSigning.objects.create(
                tenant=ten, source=M.LeaseSigning.SOURCE_UPLOADED,
                status=M.LeaseSigning.DRAFT, created_by=user,
                expires_at=timezone.now() + dt.timedelta(days=7))
            env.original_pdf.save('lease.pdf', ContentFile(a_pdf(2)),
                                  save=True)
            env.page_count = lease_sealing.render_pages(env)
            env.save(update_fields=['page_count'])
            ok(env.page_count == 2,
               'the fixture is a real two-page lease, rendered to images '
               'by ES-2', env.page_count)

            house = M.LeaseSigningParty.objects.create(
                signing=env, role=M.LeaseSigningParty.ROLE_ALIVENTE,
                order=0, name='Demetri Manias', email='signer@example.com')
            t1 = M.LeaseSigningParty.objects.create(
                signing=env, role=M.LeaseSigningParty.ROLE_TENANT,
                order=1, name='Mr. Dorian Tirouard',
                email='dorian.tirouard@example.com')
            t2 = M.LeaseSigningParty.objects.create(
                signing=env, role=M.LeaseSigningParty.ROLE_TENANT,
                order=2, name='Mr. Antoine Madelbos',
                email='antoine.madelbos@example.com')

            # SERVER_NAME, AND NOT testserver. Django's own test
            # runner adds 'testserver' to ALLOWED_HOSTS; a bare Client
            # outside a TestCase gets no such favour, and every request
            # came back 400 DisallowedHost - which reads exactly like a
            # broken view. 'localhost' is in this project's real
            # ALLOWED_HOSTS, so the suite asks the application the same
            # question a browser on the laptop would.
            HOST = {'SERVER_NAME': 'localhost'}
            c = Client(**HOST)

            # ---- (a) THE HOUSE SIGNS, SIGNED IN, WITH NO EMAIL AT ALL.
            c.force_login(user)
            r = c.get('/lease-signing/%d/sign/' % env.pk)
            ok(r.status_code == 200,
               'the named Alivente signer reaches the page while signed '
               'in - no link, no round trip', r.status_code)
            body = r.content.decode('utf-8', 'replace')
            ok('read the whole agreement' in body.lower(),
               '  and is told to read it to the end before anything else')

            # SOMEBODY ELSE SIGNED IN IS NOT THE SIGNER.
            other = User.objects.create_user(
                username='es4other', password='not-a-real-password',
                email='nobody@example.com')
            c2 = Client(**HOST)
            c2.force_login(other)
            ok(c2.get('/lease-signing/%d/sign/' % env.pk).status_code == 404,
               '  while a DIFFERENT signed-in user is refused - the '
               'envelope names a person, and signing on their behalf '
               'would put a name on a lease that nobody with that name '
               'typed')

            mail.outbox = []
            r = c.post('/lease-signing/%d/sign/' % env.pk, {
                'consent': '1', 'read_to_end': '1', 'seconds_open': '95',
                'signature_kind': 'typed', 'typed_name': 'Demetri Manias'})
            ok(r.status_code == 200, 'the house signature is accepted',
               r.status_code)

            house.refresh_from_db()
            env.refresh_from_db()
            ok(bool(house.signed_at), '  and is recorded')
            ok(house.signed_auth == M.LeaseSigningParty.AUTH_SESSION,
               '  as a SESSION, which is the stronger evidence - ES-1 '
               'refused a model that could not tell the two apart',
               house.signed_auth)
            ok(house.signed_by_user_id == user.pk,
               '  naming the user, which a token signature never can')
            ok(house.signature_kind == M.LeaseSigningParty.KIND_TYPED,
               '  and says the signature was typed, not drawn',
               house.signature_kind)

            # ---- (b) AND THAT IS WHAT SENT IT.
            ok(env.status == M.LeaseSigning.SENT,
               'the house signature moved the envelope to out-for-'
               'signature - "it is only then sent to the tenant"',
               env.status)
            ok(bool(env.sent_at), '  with a sent date')
            to = sorted(sum([list(m.to) for m in mail.outbox], []))
            ok(to == ['antoine.madelbos@example.com',
                      'dorian.tirouard@example.com'],
               '  and BOTH tenants were emailed, each at their own '
               'address - decision 6 of 22 October', to)
            ok(len(mail.outbox) == 2,
               '  one message each, not one message to both', len(mail.outbox))
            links = re.findall(r'https?://[^\s]+/sign/([A-Za-z0-9_-]+)/',
                               '\n'.join(m.body for m in mail.outbox))
            ok(len(links) == 2 and links[0] != links[1],
               '  carrying two DIFFERENT links, so the trail can tell '
               'them apart', links)
            # len() FIRST. all() over an empty list is True, so with
            # no outbox this reported that every email said the right
            # thing - the 23 October lesson again, in a third shape.
            ok(len(mail.outbox) == 2
               and all('read the agreement to the end' in m.body.lower()
                       for m in mail.outbox),
               '  and the email says so too, before they even open it')

            # THE RAW TOKEN IS NOWHERE IN THE DATABASE.
            t1.refresh_from_db()
            ok(t1.token_hash and t1.token_hash not in links,
               'the raw token is NOT what is stored - only its sha256, '
               'which is why a resend can kill the old link')
            tok = [l for l in links
                   if M.LeaseSigningParty.hash_token(l) == t1.token_hash]
            ok(len(tok) == 1, '  and the stored hash identifies its owner')
            if not tok:
                raise AssertionError(
                    'no link in the outbox hashes to the stored token, so '
                    'nothing below this point can be asked at all')
            tok1 = tok[0]
            tok2 = [l for l in links if l != tok1][0]

            # ---- (c) A TENANT OPENS THE LINK.
            pub = Client(**HOST)
            r = pub.get('/sign/%s/' % tok1)
            ok(r.status_code == 200,
               'a tenant opens the link with no account at all',
               r.status_code)
            body = r.content.decode('utf-8', 'replace')
            ok('Already signed by' in body,
               '  and is shown that Alivente has already signed - which '
               'is the whole reason the house signs first')
            ok('noindex' in body,
               '  on a page no search engine is invited to keep')
            t1.refresh_from_db()
            ok(t1.view_count == 1 and bool(t1.first_viewed_at),
               '  and the opening is recorded', t1.view_count)


            # ==========================================================
            head('4. THE LOCK, ASKED THE WAY AN ATTACKER WOULD ASK IT')
            # ==========================================================
            #
            # The button is disabled until the last page has been on
            # screen. A disabled button is a courtesy to somebody using
            # the page; it is not a check. So this posts without the
            # flag, which is what a hand-rolled request looks like.
            png = (b'\x89PNG\r\n\x1a\n' + b'\x00' * 600)
            import base64 as _b64
            drawn = ('data:image/png;base64,'
                     + _b64.b64encode(png).decode('ascii'))

            r = pub.post('/sign/%s/' % tok1, {
                'consent': '1', 'seconds_open': '40',
                'signature_kind': 'drawn', 'signature_data': drawn})
            t1.refresh_from_db()
            ok(r.status_code == 400 and not t1.signed_at,
               'a signature posted WITHOUT having read to the end is '
               'refused by the server, not merely greyed out on the page',
               r.status_code)
            ok('read the agreement to the end' in
               r.content.decode('utf-8', 'replace').lower(),
               '  and the refusal says what was missing')

            r = pub.post('/sign/%s/' % tok1, {
                'read_to_end': '1', 'seconds_open': '40',
                'signature_kind': 'drawn', 'signature_data': drawn})
            t1.refresh_from_db()
            ok(r.status_code == 400 and not t1.signed_at,
               'and a signature with no consent ticked is refused too',
               r.status_code)

            # AN EMPTY CANVAS STILL PRODUCES A PNG, which is why the
            # view measures the bytes rather than trusting the prefix.
            tiny = ('data:image/png;base64,'
                    + _b64.b64encode(b'\x89PNG\r\n\x1a\n' + b'\x00' * 20)
                    .decode('ascii'))
            r = pub.post('/sign/%s/' % tok1, {
                'consent': '1', 'read_to_end': '1', 'seconds_open': '40',
                'signature_kind': 'drawn', 'signature_data': tiny})
            t1.refresh_from_db()
            ok(r.status_code == 400 and not t1.signed_at,
               'an EMPTY signature box is refused - a blank canvas is '
               'still a valid PNG, and it would print as a blank '
               'rectangle on the signature page', r.status_code)

            # AND SOMETHING THAT IS NOT AN IMAGE AT ALL.
            bad = ('data:image/png;base64,'
                   + _b64.b64encode(b'<svg onload=alert(1)>' + b'x' * 600)
                   .decode('ascii'))
            r = pub.post('/sign/%s/' % tok1, {
                'consent': '1', 'read_to_end': '1', 'seconds_open': '40',
                'signature_kind': 'drawn', 'signature_data': bad})
            t1.refresh_from_db()
            ok(r.status_code == 400 and not t1.signed_at,
               'and so is anything that is not a PNG, whatever the data '
               'URL claims', r.status_code)

            # ---- NOW, PROPERLY.
            mail.outbox = []
            r = pub.post('/sign/%s/' % tok1, {
                'consent': '1', 'read_to_end': '1', 'seconds_open': '137',
                'signature_kind': 'drawn', 'signature_data': drawn},
                HTTP_USER_AGENT='Mozilla/5.0 (iPhone)',
                HTTP_X_FORWARDED_FOR='203.0.113.9, 10.0.0.1')
            ok(r.status_code == 200, 'a complete signature is accepted',
               r.status_code)

            t1.refresh_from_db()
            env.refresh_from_db()
            ok(bool(t1.signed_at), '  and recorded')
            ok(t1.signed_auth == M.LeaseSigningParty.AUTH_TOKEN,
               '  as a LINK HOLDER, which is the honest limit of what '
               'the system can say about a tenant', t1.signed_auth)
            ok(t1.signed_ip == '203.0.113.9',
               '  taking the address from the proxy header, because '
               'Railway terminates TLS in front of the application and '
               'REMOTE_ADDR is the proxy for everybody', t1.signed_ip)
            ok('iPhone' in (t1.signed_user_agent or ''),
               '  with the browser it came from', t1.signed_user_agent)
            ok(t1.read_to_end and t1.seconds_open == 137,
               '  and how long it was open, which with no certificate '
               'is the difference between somebody having the link and '
               'somebody having read the lease', t1.seconds_open)
            ok(bool(t1.signature_image), '  and the drawn image is stored')
            ok(env.status == M.LeaseSigning.PART,
               'the envelope is PART SIGNED, not complete - one of two '
               'tenants has signed', env.status)
            ok(mail.outbox == [],
               '  and nothing was emailed, because nothing finished')

            # A SIGNED LINK IS SPENT.
            r = pub.get('/sign/%s/' % tok1)
            ok(r.status_code in (200, 410),
               '  the used link still resolves rather than 404ing',
               r.status_code)


            # ==========================================================
            head('4b. THE LOCK, IN A BROWSER')
            # ==========================================================
            #
            # SHIPPED LOCKED, AND IT WAS NOT. Section 4 proves the
            # SERVER refuses an unread signature. This proves the page
            # does not hand the reader an unlocked button in the first
            # place - and the first build of this round did exactly
            # that, for a reason no amount of reading the markup would
            # have shown:
            #
            #     the page images are lazy, a lazy image that has not
            #     loaded is ZERO PIXELS TALL, all three pages stacked
            #     at the same y, the end-of-document sentinel was in
            #     the viewport on arrival, the observer fired, and the
            #     button unlocked before anybody had read a word.
            #
            # Caught in a desktop render. The fix is an aspect-ratio
            # on .ls-page so the document has its true height before
            # the first byte of an image arrives, and THIS is the
            # check that keeps it.
            try:
                from playwright.sync_api import sync_playwright
                import alv_offline                   # noqa: F401
            except Exception:
                sync_playwright = None

            if sync_playwright is None:
                skip('section 4b', 'playwright is not installed')
            else:
                import base64 as _b
                page_html = pub2_get = Client(**HOST).get(
                    '/sign/%s/' % tok2).content.decode('utf-8', 'replace')
                for n in range(1, env.page_count + 1):
                    u = '/sign/%s/page/%d/' % (tok2, n)
                    img = Client(**HOST).get(u).content
                    page_html = page_html.replace(
                        'src="%s"' % u,
                        'src="data:image/png;base64,%s"'
                        % _b.b64encode(img).decode('ascii'))
                scratch = (os.environ.get('ALV_SCRATCH')
                           or os.path.join(ROOT, '_scratch'))
                if not os.path.isdir(scratch):
                    os.makedirs(scratch)
                fx = os.path.join(scratch, '_es4_sign.html')
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write(page_html)

                exe = os.path.join(ROOT, 'chromium', 'chrome.exe')
                with sync_playwright() as _pw:
                    _br = _pw.chromium.launch(
                        **({'executable_path': exe}
                           if os.path.exists(exe) else {}))
                    for width, where in ((1280, 'DESK'), (390, 'PHONE')):
                        _c = _br.new_context(
                            viewport={'width': width, 'height': 900})
                        _p = _c.new_page()
                        _p.goto('file://' + fx.replace(os.sep, '/'))
                        _p.wait_for_timeout(500)
                        st = _p.evaluate("""() => ({
                          disabled: document.getElementById('ls-sign').disabled,
                          why: document.getElementById('ls-why').textContent,
                          progress: document.getElementById(
                              'ls-progress-text').textContent,
                          read: document.getElementById('ls-read').value
                        })""")
                        ok(st['disabled'],
                           '%s: the page ARRIVES with signing locked'
                           % where, st)
                        ok(st['read'] == '0',
                           '  and has not decided the reader reached the '
                           'end', st)
                        ok('read to the end' in st['why'],
                           '  saying so, rather than sitting grey and '
                           'silent - which is the half he asked for',
                           st['why'])
                        ok(st['progress'].startswith('Page 1 '),
                           '  and the progress strip starts at page one, '
                           'not at the last one', st['progress'])

                        _p.evaluate(
                            'window.scrollTo(0, document.body.scrollHeight)')
                        _p.wait_for_timeout(600)
                        st = _p.evaluate("""() => ({
                          read: document.getElementById('ls-read').value,
                          why: document.getElementById('ls-why').textContent
                        })""")
                        ok(st['read'] == '1',
                           '  and reaching the end unlocks that half',
                           st)
                        ok('read to the end' not in st['why'],
                           '  with the control no longer asking for it',
                           st['why'])
                        _c.close()
                    _br.close()


            # ==========================================================
            head('5. WHAT MUST NOT LEAK')
            # ==========================================================
            #
            # A seven-day link to a contract that outlives its own
            # expiry is the failure this round is most able to ship.
            r = pub.get('/sign/%s/page/1/' % tok2)
            ok(r.status_code == 200
               and r['Content-Type'] == 'image/png',
               'a page of the lease comes back through the token check',
               r.status_code)
            ok(r.content[:8] == b'\x89PNG\r\n\x1a\n',
               '  and is really the rendered page')
            ok('no-store' in r.get('Cache-Control', ''),
               '  uncached by anything in between, because a shared '
               'cache holding it is the same leak as a media URL',
               r.get('Cache-Control', ''))

            ok(pub.get('/sign/not-a-token/page/1/').status_code == 404,
               'an unknown token gets no page at all')
            ok(pub.get('/sign/%s/page/99/' % tok2).status_code == 404,
               'and nor does a page that does not exist')

            # AND NO MEDIA URL ANYWHERE ON THE PAGE.
            body = pub.get('/sign/%s/' % tok2).content.decode(
                'utf-8', 'replace')
            ok('/media/' not in body,
               'the signing page reaches the lease through no media URL '
               '- which would be a permanent read link to a contract')


            # ==========================================================
            head('6. THE LAST SIGNATURE SEALS IT')
            # ==========================================================
            mail.outbox = []
            pub2 = Client(**HOST)
            r = pub2.post('/sign/%s/' % tok2, {
                'consent': '1', 'read_to_end': '1', 'seconds_open': '88',
                'signature_kind': 'typed',
                'typed_name': 'Mr. Antoine Madelbos'})
            ok(r.status_code == 200, 'the second tenant signs',
               r.status_code)

            env.refresh_from_db()
            ok(env.status == M.LeaseSigning.COMPLETED,
               '  and the envelope is COMPLETE', env.status)
            ok(bool(env.completed_at), '  with a completion date')
            ok(bool(env.sealed_pdf) and bool(env.pdf_sha256),
               '  sealed, with the hash of the bytes that were stored - '
               'which with no certificate IS the tamper evidence')
            ok(len(env.pdf_sha256) == 64,
               '  a full sha256', len(env.pdf_sha256 or ''))
            ok(env.sealed_pdf.name.endswith('lease-%d.pdf' % env.pk),
               '  on the name ES-2a gave it, built from the primary key',
               env.sealed_pdf.name)

            ok(len(mail.outbox) == 1,
               'one copy of the signed agreement goes out', len(mail.outbox))
            if mail.outbox:
                m = mail.outbox[0]
                ok(sorted(m.to) == ['antoine.madelbos@example.com',
                                    'dorian.tirouard@example.com'],
                   '  to every address on the tenancy, which T2-5 made '
                   'one expression on the model', sorted(m.to))
                ok(len(m.attachments) == 1
                   and m.attachments[0][0].endswith('.pdf'),
                   '  with the sealed PDF attached',
                   [a[0] for a in m.attachments])

            kinds = list(env.events.order_by('at')
                         .values_list('kind', flat=True))
            for want in ('viewed', 'consented', 'signed', 'sent',
                         'sealed', 'delivered'):
                ok(want in kinds, '  the trail records %r' % want, kinds)
            ok(kinds.index('sent') < kinds.index('sealed'),
               '  in an order that happened - sent before sealed', kinds)


            # ==========================================================
            head('7. AFTER THE DATE')
            # ==========================================================
            #
            # Decided 24 October, both halves: NOT a silent 404, because
            # a tenant who was merely slow would not know whether they
            # had the wrong link or missed a deadline - and NOT the
            # document either, because that turns seven days into for
            # ever.
            gone = M.LeaseSigning.objects.create(
                tenant=ten, source=M.LeaseSigning.SOURCE_UPLOADED,
                status=M.LeaseSigning.SENT, created_by=user,
                expires_at=timezone.now() - dt.timedelta(days=1))
            gone.original_pdf.save('old.pdf', ContentFile(a_pdf(1)),
                                   save=True)
            gone.page_count = lease_sealing.render_pages(gone)
            gone.save(update_fields=['page_count'])
            gp = M.LeaseSigningParty.objects.create(
                signing=gone, role=M.LeaseSigningParty.ROLE_TENANT,
                order=1, name='Mr. Dorian Tirouard',
                email='dorian.tirouard@example.com')
            graw = gp.issue_token()
            gp.save(update_fields=['token_hash', 'token_issued_at'])

            r = pub.get('/sign/%s/' % graw)
            body = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 410,
               'an expired link answers 410 Gone - the thing was here '
               'and is not, which is neither a 404 nor a pretence that '
               'it still works', r.status_code)
            ok('signing period' in body.lower(),
               '  and says the period ended, rather than going silent')
            ok('/page/' not in body and '<form' not in body,
               '  showing no document and offering no controls')

            r = pub.post('/sign/%s/' % graw, {
                'consent': '1', 'read_to_end': '1',
                'signature_kind': 'typed', 'typed_name': 'Dorian Tirouard'})
            gp.refresh_from_db()
            ok(r.status_code == 410 and not gp.signed_at,
               'and a signature posted after the date is refused',
               r.status_code)
            ok(pub.get('/sign/%s/page/1/' % graw).status_code == 404,
               'and the pages are gone with it - an expired link is not '
               'a read link')

            raise Rollback
    except Rollback:
        pass
    finally:
        over.disable()
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
head('8. THE COPIED TOKENS STILL MATCH base.html')
# ==========================================================================
#
# THIS IS WHAT EARNS THE STANDALONE DECISION. Four public templates
# cannot extend base.html, which puts them outside every colour census
# in this tree - test_amber, test_brights, the four test_colour_*
# suites, test_cssrules_outside and test_dead_weight all skip
# standalone pages. Nothing else will ever notice one of these values
# drifting, so this suite takes the job.
css = read(BASE)
styles = read(STYLES)
pairs = re.findall(r'(?m)^\s*(--alv-[a-z-]+):\s*(#[0-9a-fA-F]{3,8});',
                   styles)
ok(len(pairs) >= 20,
   'the public pages define their own tokens, %d of them' % len(pairs))
drift = []
for name, value in pairs:
    m = re.search(r'(?m)^\s*%s:\s*([^;]+);' % re.escape(name), css)
    if m is None:
        drift.append('%s is not in base.html at all' % name)
    elif m.group(1).strip().lower() != value.lower():
        drift.append('%s is %s in base and %s here'
                     % (name, m.group(1).strip(), value))
ok(drift == [],
   '  and every one of them is the value base.html gives it', drift)

for p in (SIGN, DONE, CLOSED):
    body = T.code_only_js(read(p))
    ok('{% include' in body and 'lease_sign_styles.html' in body,
       '%s takes the one shared copy rather than its own'
       % os.path.basename(p))
    ok('{% extends' not in body,
       '  and extends nothing, because a tenant holding a link is not '
       'signed in and base queries for a navbar they will never see')

sa = T.standalone()
ok(len(sa) == 18,
   'alv_tree counts 18 standalone templates, the four of them included',
   len(sa))
for p in (SIGN, DONE, CLOSED, STYLES):
    ok(T.rel(p).replace(os.sep, '/') in sa,
       '  %s among them' % os.path.basename(p))


# ==========================================================================
head('9. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('def lease_sign_page' in gate,
   '  with a sentinel that would notice the document leaving the token '
   'check')
ok('read_to_end' in gate,
   '  and one that would notice the lock becoming decoration')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(n and int(n.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (n.group(1) if n else '?', len(T.CONVERTED)))

ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
import importlib                                            # noqa: E402
_p = importlib.import_module(PATCHER[:-3])
ok(sorted(os.path.basename(x) for x in _p.CREATES)
   == sorted(os.path.basename(x) for x in SHIPPED),
   '  and declares every file it ships, so stage_round cannot leave '
   'one behind - which is exactly what PF-2 did on 19 October',
   list(_p.CREATES))
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
