# -*- coding: utf-8 -*-
"""test_signing_lifecycle.py - round ES-5, 25 Oct 2026.

WHAT HAPPENS TO AN ENVELOPE AFTER IT IS SENT, DRIVEN.

Reminders on day 3 and day 6 to whoever has not signed; expiry that
marks and keeps; extend that gives seven more days and a fresh link to
the outstanding parties only; decline that ends the envelope for
everybody and tells him; cancel that keeps every signature and stops
the links. All of it decided with him before a line was written -
claude/es5_es6_decisions_25_oct.md and the 24 October expiry note.

THE CLOCK IS AN ARGUMENT, NOT A SLEEP. The tick's two jobs take `now`,
so section 3 walks one envelope through day 2, 3, 3 again, 6 and 6
again in a second, and asks after each step who was emailed. A suite
that waited for days would never run; one that faked the system clock
would be testing the fake.

THE CLAIM WITH TEETH IS "NEVER EMAILED AGAIN". Whoever has signed is
not reminded and gets no extension email - his rule, and the one a
careless loop over parties breaks first. Every mail step counts the
recipients by name.

WHAT IS NOT PROVED HERE. That Railway's cron runs the command it is
hooked into. The hook sits beside send_physical_invoices in
check_lease_renewal_and_invoices, which the invoices prove runs; what
railway.json itself names is a separate question, recorded in the
round's note.
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

import io
import os
import re
import shutil
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_signlife'
ME = 'test_signing_lifecycle.py'
PATCHER = 'apply_signing_lifecycle.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-5, 25 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
SIGN = os.path.join(ROOT, 'pages', 'views', 'lease_signing_sign.py')
REG_VIEW = os.path.join(ROOT, 'pages', 'views', 'lease_signing.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
REG_PAGE = os.path.join(ROOT, 'pages', 'templates', 'lease_signing_list.html')
SIGN_PAGE = os.path.join(ROOT, 'pages', 'templates', 'lease_sign.html')
CLOSED = os.path.join(ROOT, 'pages', 'templates', 'lease_sign_closed.html')
CRON = os.path.join(ROOT, 'pages', 'management', 'commands',
                    'check_lease_renewal_and_invoices.py')
TICK = os.path.join(ROOT, 'pages', 'management', 'commands',
                    'lease_signing_tick.py')
MIG = os.path.join(ROOT, 'pages', 'migrations',
                   '0106_es5_signing_lifecycle.py')
GATE = os.path.join(ROOT, PS1)

EDITED = (MODELS, SIGN, REG_VIEW, URLS, REG_PAGE, SIGN_PAGE, CLOSED, CRON)
SHIPPED = (TICK, MIG)

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


def claims(src):
    py = dict((p, T.python_code_only(src[p])) for p in
              (MODELS, SIGN, REG_VIEW, URLS, CRON))
    mk = dict((p, T.code_only_js(src[p])) for p in
              (REG_PAGE, SIGN_PAGE, CLOSED))
    return [
        ("DECLINED = 'declined'" in py[MODELS],
         'an envelope can be DECLINED'),
        ("('extended', 'Extended')" in py[MODELS],
         'and the trail can say it was EXTENDED'),
        # ES-6, 25 Oct 2026 - day 3 and the day before it lapses, which
        # for the usual seven days IS day 3 and day 6; the fixed pair
        # broke on any other window the Send screen allows.
        ('FIRST_REMINDER_DAY = 3' in py[MODELS]
         and 'LAST_REMINDER_DAYS_BEFORE = 1' in py[MODELS],
         'reminders are day 3 and the day before it lapses, written once '
         'on the model'),
        ('def outstanding(self)' in py[MODELS]
         and 'def reminder_due(self' in py[MODELS],
         'one answer to "who are we waiting for", and one to "is a '
         'reminder due"'),
        ('link_base = models.CharField' in py[MODELS],
         'the envelope remembers where its links point, for the cron'),
        ("why='sent'" in py[SIGN] and "why == 'reminder'" in py[SIGN],
         'ONE mint-and-send function for invitation, reminder and '
         'extension'),
        ("request.POST.get('action') == 'decline'" in py[SIGN]
         and 'def _decline(' in py[SIGN],
         'the signing page takes a decline'),
        ('def lease_signing_extend(' in py[REG_VIEW]
         and 'def lease_signing_cancel(' in py[REG_VIEW],
         'the register can extend and cancel'),
        ("name='lease_signing_extend'" in py[URLS]
         and "name='lease_signing_cancel'" in py[URLS],
         '  and both are routed'),
        ("{% url 'lease_signing_extend' r.env.pk %}" in mk[REG_PAGE]
         and "{% url 'lease_signing_cancel' r.env.pk %}" in mk[REG_PAGE],
         '  and the icons drawn on 23 October now POST somewhere'),
        ('name="action" value="decline"' in mk[SIGN_PAGE],
         'the signing page offers Decline'),
        ('{% if declined %}' in mk[CLOSED],
         'the closed page knows a declined envelope'),
        ("call_command('lease_signing_tick'" in py[CRON],
         'the five-minute job runs the tick'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
mig = T.python_code_only(NOW[MIG])
ok(mig.count('migrations.AddField(') == 1
   and mig.count('migrations.AlterField(') == 2
   and 'RunPython' not in mig and 'RunSQL' not in mig,
   'the migration is one AddField and two choice changes - no data '
   'touched')
ok('"0105_es2a_sealed_name"' in mig,
   '  and follows the one immediately before it')
ok(all(MARK in NOW[p] for p in EDITED + (TICK,)),
   'the round dates itself in every file it touched')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
_old = dict(OLD)
_old.update((p, '') for p in SHIPPED)
held = [m for c, m in claims(_old) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))
ok('<span class="icon-action-btn icon-cancel" title="Cancel">' in OLD[REG_PAGE],
   'CONTROL: the register really did draw a Cancel that did nothing')
ok('EXPIRY IS READ, NOT WRITTEN' in OLD[REG_VIEW],
   'CONTROL: and really did leave expiry for this round to write')
for p in SHIPPED:
    ok(not os.path.isfile(p + SUFFIX),
       'CONTROL: %s has no backup, because this round INVENTED it'
       % os.path.basename(p))


# ==========================================================================
# THE DRIVEN SECTIONS
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.contrib.auth.models import Permission, User
    from django.core import mail
    from django.core.files.base import ContentFile
    from django.db import transaction
    from django.test import Client
    from django.test.utils import override_settings
    from django.utils import timezone
    import pages.models as M
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('sections 3 to 8', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


class Rollback(Exception):
    """Nothing this suite writes survives it."""


have_db = False
if django_up:
    try:
        from django.db import connection
        connection.ensure_connection()
        M.LeaseSigning.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('sections 3 to 8, the whole driven flow',
             'no database: %s' % str(_e).split('\n')[0][:70])


def a_pdf():
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 110), 'LEASE AGREEMENT', fontsize=18)
    raw = doc.tobytes()
    doc.close()
    return raw


def to_whom():
    """Every address emailed since the outbox was last emptied."""
    out = []
    for m in mail.outbox:
        out.extend(m.to)
    return sorted(out)


if have_db:
    tmp = tempfile.mkdtemp(prefix='alv_es5_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    from django.core.management import call_command
    from pages.management.commands.lease_signing_tick import Command as Tick
    from pages.views.lease_signing_sign import _by_token  # noqa: F401
    try:
        with transaction.atomic():
            HOST = {'SERVER_NAME': 'localhost'}
            user = User.objects.create_user(
                username='es5house', password='not-a-real-password',
                email='house@example.com', first_name='Demetri',
                last_name='Manias')
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(Permission)
            for code in ('can_edit_tenants', 'can_access_tenants'):
                perm = Permission.objects.get_or_create(
                    codename=code,
                    defaults={'name': code, 'content_type': ct})[0]
                user.user_permissions.add(perm)
            # ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY (his
            # decision), so the account driving these screens is one.
            user.is_superuser = True
            user.save()
            staff = Client(**HOST)
            staff.force_login(user)

            n_prop = [0]

            def envelope(status, days_left=7, signed=()):
                """One joint tenancy, one envelope, house already signed."""
                n_prop[0] += 1
                prop = M.props.objects.create(
                    prop_name='Flat %d, Palikaridi' % n_prop[0],
                    prop_country='Cyprus')
                ten = M.tenant.objects.create(
                    prop=prop, tenant_type='Individual',
                    tenant_name='Andreas Georgiou',
                    tenant_email='andreas@example.com',
                    tenant_2_name='Maria Georgiou',
                    tenant_2_email='maria@example.com',
                    tenant_lease_start_date=timezone.now().date(),
                    tenant_lease_end_date=(timezone.now()
                                           + timezone.timedelta(days=365)
                                           ).date(),
                    tenant_current='Yes')
                now = timezone.now()
                env = M.LeaseSigning(
                    tenant=ten, status=status, created_by=user,
                    sent_at=now, page_count=1,
                    expires_at=now + timezone.timedelta(days=days_left),
                    link_base='http://localhost')
                env.save()
                env.original_pdf.save('lease.pdf', ContentFile(a_pdf()),
                                      save=True)
                house = M.LeaseSigningParty.objects.create(
                    signing=env, role='alivente', order=0,
                    name='Demetri Manias', email='house@example.com',
                    signed_at=now, signature_kind='typed',
                    typed_name='Demetri Manias', signed_auth='session')
                a = M.LeaseSigningParty.objects.create(
                    signing=env, role='tenant', order=1,
                    name='Andreas Georgiou', email='andreas@example.com')
                b = M.LeaseSigningParty.objects.create(
                    signing=env, role='tenant', order=2,
                    name='Maria Georgiou', email='maria@example.com')
                links = {}
                for p in (a, b):
                    links[p.pk] = p.issue_token()
                    p.save()
                for p in (a, b):
                    if p.name.split()[0] in signed:
                        p.signed_at = now
                        p.signature_kind = 'typed'
                        p.typed_name = p.name
                        p.signed_ip = '203.0.113.7'
                        p.save()
                return env, house, a, b, links

            # ==============================================================
            head('3. REMINDERS - DAY 3 AND DAY 6, ONLY TO WHOEVER HAS NOT SIGNED')
            # ==============================================================
            env, house, a, b, links = envelope(M.LeaseSigning.SENT)
            start = env.expires_at - timezone.timedelta(days=7)
            at = lambda d: start + timezone.timedelta(days=d)  # noqa: E731
            tick = Tick()
            tick.stdout = io.StringIO()

            ok(env.reminder_due(at(2.9)) is None,
               'on day 2 nothing is due')
            mail.outbox = []
            tick.remind(at(2.9), False)
            ok(not mail.outbox, '  and the tick sends nothing')

            ok(env.reminder_due(at(3.01)) == 3, 'on day 3 the first is due')
            mail.outbox = []
            tick.remind(at(3.01), False)
            ok(to_whom() == ['andreas@example.com', 'maria@example.com'],
               '  and both tenants are reminded - not the house, which '
               'has signed', to_whom())
            ok(all(m.subject.startswith('Reminder:') for m in mail.outbox),
               '  as a reminder, in so many words')
            ok(all('http://localhost/sign/' in m.body for m in mail.outbox),
               '  with a link built from where the envelope was sent - the '
               'cron has no request to build one from')

            r_old = Client(**HOST).get('/sign/%s/' % links[a.pk])
            ok(r_old.status_code == 404,
               'THE OLD LINK DIES - tokens are stored hashed, so a reminder '
               'can only replace the link, never repeat it (ES-1)',
               r_old.status_code)
            new_tok = re.search(r'/sign/([^/\s]+)/', [
                m for m in mail.outbox if 'andreas' in m.to[0]][0].body)
            r_new = Client(**HOST).get('/sign/%s/' % new_tok.group(1))
            ok(r_new.status_code == 200, '  and the new one opens the page',
               r_new.status_code)

            mail.outbox = []
            tick.remind(at(3.5), False)
            ok(not mail.outbox, 'run again on day 3 and nobody is emailed '
               'twice')

            a.refresh_from_db()
            a.signed_at = timezone.now()
            a.signature_kind = 'typed'
            a.typed_name = a.name
            a.save()
            env.status = M.LeaseSigning.PART
            env.save()
            env.refresh_from_db()
            mail.outbox = []
            tick.remind(at(6.01), False)
            maria_tok = (re.search(r'/sign/([^/\s]+)/', mail.outbox[0].body)
                         .group(1) if mail.outbox else '')
            ok(to_whom() == ['maria@example.com'],
               'ON DAY 6, ONLY THE TENANT WHO HAS NOT SIGNED - Andreas '
               'signed, and a co-operative tenant is not chased for '
               'somebody else\'s silence', to_whom())
            mail.outbox = []
            tick.remind(at(6.5), False)
            ok(not mail.outbox, '  and not again the same day')

            env2, _h, _a, _b, _l = envelope(M.LeaseSigning.SENT)
            s2 = env2.expires_at - timezone.timedelta(days=7)
            mail.outbox = []
            tick.remind(s2 + timezone.timedelta(days=6.2), False)
            ok(to_whom() == ['andreas@example.com', 'maria@example.com'],
               'A CRON THAT WAS DOWN ACROSS BOTH DAYS SENDS ONE REMINDER, '
               'not two in the same minute', to_whom())
            env2.refresh_from_db()
            ok(env2.reminder_due(s2 + timezone.timedelta(days=6.3)) is None,
               '  and owes none afterwards')

            # ==============================================================
            head('4. EXPIRY MARKS THE ENVELOPE AND KEEPS EVERY SIGNATURE')
            # ==============================================================
            tick.expire(env.expires_at + timezone.timedelta(minutes=1),
                        False)
            env.refresh_from_db()
            a.refresh_from_db()
            ok(env.status == M.LeaseSigning.EXPIRED,
               'past its date, the envelope is EXPIRED - written by the '
               'tick, never by the register looking at it')
            ok(a.signed_at and a.typed_name == 'Andreas Georgiou',
               'ANDREAS\'S SIGNATURE IS STILL THERE - expiry marks, it '
               'never voids')
            ev = env.events.filter(kind='expired').first()
            ok(ev and 'Andreas Georgiou' in ev.detail
               and 'did not sign: Maria Georgiou' in ev.detail,
               '  and the trail says who signed and who did not',
               ev.detail if ev else None)
            # HER NEWEST LINK, from the day 6 reminder. Her first one
            # died when that reminder replaced it, so asking it would
            # 404 whether or not expiry worked - a claim that passes
            # because the thing is absent.
            r = Client(**HOST).get('/sign/%s/' % maria_tok)
            ok(r.status_code == 410
               and b'signing period for this agreement has ended' in r.content
               and b'/page/1/' not in r.content,
               'MARIA\'S CURRENT LINK SHOWS THE PLAIN EXPIRED PAGE - no '
               'document, no controls, and not a 404', r.status_code)

            # ==============================================================
            head('5. EXTEND - SEVEN MORE DAYS, A FRESH LINK TO THE OUTSTANDING ONLY')
            # ==============================================================
            mail.outbox = []
            before = timezone.now()
            r = staff.post('/lease-signing/%s/extend/' % env.pk)
            env.refresh_from_db()
            ok(r.status_code == 302, 'the register control answers with '
               'a redirect back to the register', r.status_code)
            ok(env.status == M.LeaseSigning.PART,
               'FROM EXPIRED IT REOPENS AS PART-SIGNED, because Andreas\'s '
               'signature was kept', env.status)
            # ES-7, 25 Oct 2026 - SEVEN DAYS FROM TODAY, TO THE END OF THAT
            # DAY in local time: his decision that a link stays open to the
            # end of the day the email names.
            close = timezone.localtime(env.expires_at)
            ok(close.date() == timezone.localdate(before)
               + timezone.timedelta(days=7)
               and (close.hour, close.minute, close.second) == (23, 59, 59),
               '  with a new date seven days from now, open to the END of '
               'that day, STORED - it is the date the email states', close)
            ok(to_whom() == ['maria@example.com'],
               'ONLY MARIA IS EMAILED. Andreas signed and gets nothing; the '
               'house signed and gets nothing', to_whom())
            ok(mail.outbox and 'extended' in mail.outbox[0].body,
               '  and the email says the time was extended')
            ev = env.events.filter(kind='extended').first()
            ok(ev and 'Demetri Manias' in ev.detail,
               '  and the trail records who extended it and to when',
               ev.detail if ev else None)

            env3, _h3, _a3, _b3, _l3 = envelope(M.LeaseSigning.DRAFT)
            r = staff.post('/lease-signing/%s/extend/' % env3.pk)
            env3.refresh_from_db()
            ok(env3.status == M.LeaseSigning.DRAFT and env3.events.filter(
                kind='extended').count() == 0,
               'a draft cannot be extended - nothing has been sent')
            ok(staff.get('/lease-signing/%s/extend/' % env.pk).status_code
               == 405, 'and a GET changes nothing - POST only')

            # ==============================================================
            head('6. DECLINE ENDS THE ENVELOPE FOR EVERYBODY, AND HE IS TOLD')
            # ==============================================================
            env4, h4, a4, b4, l4 = envelope(M.LeaseSigning.SENT)
            mail.outbox = []
            r = Client(**HOST).post('/sign/%s/' % l4[b4.pk],
                                    {'action': 'decline'})
            env4.refresh_from_db()
            b4.refresh_from_db()
            ok(env4.status == M.LeaseSigning.DECLINED,
               'a tenant who declines moves the envelope to DECLINED')
            ok(b4.declined_at is not None, '  and is recorded as the one '
               'who declined, with when')
            ok(env4.events.filter(kind='declined', party=b4).exists(),
               '  in the trail')
            ok(to_whom() == ['house@example.com'],
               'HE IS TOLD - one email, to the person who sent it',
               to_whom())
            ok(mail.outbox and 'Maria Georgiou declined' in
               mail.outbox[0].body,
               '  naming who declined', mail.outbox[0].body[:120]
               if mail.outbox else '')
            ok(r.status_code == 200 and b'You declined to sign' in r.content,
               'and Maria sees that she declined, plainly')
            r = Client(**HOST).get('/sign/%s/' % l4[a4.pk])
            ok(r.status_code == 410
               and b'declined to sign this lease agreement' in r.content
               and b'ls-sign' not in r.content,
               'ANDREAS CAN NO LONGER SIGN - his link shows the declined '
               'page and no signing controls', r.status_code)
            r = Client(**HOST).post('/sign/%s/' % l4[a4.pk], {
                'consent': '1', 'read_to_end': '1',
                'signature_kind': 'typed', 'typed_name': 'Andreas'})
            a4.refresh_from_db()
            ok(a4.signed_at is None,
               '  and a hand-posted signature is refused as well')
            ok(Client(**HOST).get('/sign/%s/page/1/' % l4[a4.pk]).status_code
               == 404, '  and the document pages stop being served')

            env5, h5, a5, b5, l5 = envelope(M.LeaseSigning.SENT)
            r = staff.post('/lease-signing/%s/sign/' % env5.pk,
                           {'action': 'decline'})
            env5.refresh_from_db()
            ok(env5.status == M.LeaseSigning.SENT,
               'THE HOUSE SIGNER CANNOT DECLINE - it withdraws with Cancel',
               env5.status)

            # ==============================================================
            head('7. CANCEL KEEPS EVERY SIGNATURE AND STOPS THE LINKS')
            # ==============================================================
            env6, h6, a6, b6, l6 = envelope(M.LeaseSigning.PART,
                                            signed=('Andreas',))
            r = staff.post('/lease-signing/%s/cancel/' % env6.pk)
            env6.refresh_from_db()
            a6.refresh_from_db()
            ok(env6.status == M.LeaseSigning.CANCELLED
               and env6.cancelled_by_id == user.pk
               and env6.cancelled_at is not None,
               'cancelled, by whom and when')
            ok(a6.signed_at is not None and a6.signed_ip == '203.0.113.7',
               'ANDREAS\'S SIGNATURE IS KEPT, with where it was made from - '
               'the same rule as expiry')
            ev = env6.events.filter(kind='cancelled').first()
            ok(ev and '2 signatures kept' in ev.detail,
               '  and the trail says so', ev.detail if ev else None)
            r = Client(**HOST).get('/sign/%s/' % l6[b6.pk])
            ok(r.status_code == 410 and b'withdrawn' in r.content,
               'Maria\'s link shows the withdrawn page at once - not a 404, '
               'so she knows what happened', r.status_code)

            env7, _h7, _a7, _b7, _l7 = envelope(M.LeaseSigning.COMPLETED)
            staff.post('/lease-signing/%s/cancel/' % env7.pk)
            env7.refresh_from_db()
            ok(env7.status == M.LeaseSigning.COMPLETED,
               'a signed envelope cannot be cancelled')

            # ==============================================================
            head('8. THE REGISTER AND THE CRON')
            # ==============================================================
            r = staff.get('/lease-signing/?all=1')
            page = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200 and 'alv-pill-bad' in page
               and '>Declined<' in page,
               'the register shows a declined envelope in red')
            ok(page.count("/extend/") >= 1 and page.count('/cancel/') >= 1,
               '  and offers the controls on the rows that may take them')
            env8, _h8, _a8, _b8, _l8 = envelope(M.LeaseSigning.SENT,
                                                days_left=-1)
            call_command('lease_signing_tick', dry_run=True,
                         stdout=io.StringIO())
            env8.refresh_from_db()
            ok(env8.status == M.LeaseSigning.SENT,
               '--dry-run writes nothing')
            call_command('lease_signing_tick', stdout=io.StringIO())
            env8.refresh_from_db()
            ok(env8.status == M.LeaseSigning.EXPIRED,
               '  and the real run expires what is past its date')

            raise Rollback
    except Rollback:
        pass
    finally:
        over.disable()
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
head('9. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'if p.name.split" not in gate
   and "Text = 'def outstanding(self):'" in gate,
   '  with a sentinel that would notice "never emailed again" losing its '
   'one home')
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
   'one behind', list(_p.CREATES))
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
