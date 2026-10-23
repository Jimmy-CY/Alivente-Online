# -*- coding: utf-8 -*-
"""test_esign_model.py - round ES-1, 23 Oct 2026.

E-SIGNING, RUNG ONE: THREE TABLES AND NOTHING ELSE.

No view, no screen, no email, no route. A model round that also
shipped a screen would be two claims in one, and when the sweep went
red neither half could say which.

THE TWO THINGS WORTH DRIVING RATHER THAN READING.

ONE, THE TOKEN. The emailed link is the credential - there is no
login, decided 23 October - so a readable token column would be a
password in the clear. Section 3 mints one, proves the raw value
cannot be recovered from the row, proves a second mint produces a
different token and kills the first, and proves the lookup works by
hashing the candidate rather than by comparing stored secrets.

TWO, THE TRAIL. With no certificate, LeaseSigningEvent and
LeaseSigning.pdf_sha256 ARE the evidence - nothing in the PDF proves
anything. Section 4 drives a whole envelope's life and reads the trail
back in order, and asks the one question that matters about an
append-only table: does deleting an envelope take its events, and does
deleting a PARTY leave them standing?

WHAT IS DELIBERATELY NOT HERE. No signing page, no sealer, no email.
Those are ES-2 upward. This round is the shape of the data.
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

import glob
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_esignmodel'
ME = 'test_esign_model.py'
PATCHER = 'apply_esign_model.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-1, 23 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
MIG = os.path.join(ROOT, 'pages', 'migrations',
                   '0103_es1_lease_signing.py')
GATE = os.path.join(ROOT, PS1)
FILES = (MODELS,)

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

NOW = dict((p, read(p)) for p in FILES)


def klass(src, name):
    code = T.python_code_only(src, payloads=True)
    a = code.find('class %s(' % name)
    if a < 0:
        return ''
    body = code[a:]
    nxt = re.search(r'\nclass \w+', body[1:])
    return body[:nxt.start() + 1] if nxt else body


def claims(d):
    m = d[MODELS]
    party = klass(m, 'LeaseSigningParty')
    ev = klass(m, 'LeaseSigningEvent')
    ten = klass(m, 'tenant')
    return {
        'there is an envelope':
            bool(klass(m, 'LeaseSigning')),
        'there is a party per signer':
            bool(party),
        'there is an append-only event':
            bool(ev),
        '  and the event has no auto_now field':
            bool(ev) and 'auto_now=True' not in ev,
        'the token is stored HASHED':
            'token_hash' in party and 'sha256' in party,
        '  and there is no bare token column':
            bool(party) and not re.search(r'\n    token = models\.', party),
        '  minted from secrets, not random':
            'secrets' in party,
        'and the trail says HOW they were authenticated':
            'signed_auth' in party and 'signed_by_user' in party,
        'the envelope keeps the sha256 of what was sealed':
            'pdf_sha256' in klass(m, 'LeaseSigning'),
        'and NOTHING landed on tenant':
            bool(ten) and 'signing' not in ten and 'envelope' not in ten,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

# NL-1's CAP IS INHERITED, NOT REDISCOVERED.
m_all = T.python_code_only(NOW[MODELS], payloads=True)
ok(m_all.count('[:NAME_SLUG_CAP]') >= 5,
   'the e-signing upload paths bound their slug with NL-1\'s cap - '
   'inherited rather than rediscovered',
   m_all.count('[:NAME_SLUG_CAP]'))


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(held == ['and NOTHING landed on tenant'],
   'CONTROL: only the NEGATIVE claim held before this round - '
   'everything it adds is new, and the one thing it promises not to '
   'do was already true', held)


# ==========================================================================
head('3. DRIVEN - the token, which is the credential')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if not django_up:
    skip('sections 3 and 4', 'no database')
else:
    import datetime as dt
    from django.contrib.auth.models import User
    from django.core.files.base import ContentFile
    from django.utils import timezone
    from pages.models import (LeaseSigning, LeaseSigningParty,
                              LeaseSigningEvent, props,
                              tenant as Tenant)

    try:
        me = User.objects.create_superuser('es1', 'es1@x.test', 'x')
        p = props.objects.create(prop_name='Flat 3, Nikis Avenue',
                                 prop_country='Cyprus')
        t = Tenant.objects.create(tenant_name='Andreas Georgiou', prop=p)

        env = LeaseSigning.objects.create(tenant=t, created_by=me)
        env.original_pdf.save('lease.pdf', ContentFile(b'%PDF-1.4 fake'),
                              save=True)
        ok(env.pk and env.status == LeaseSigning.DRAFT,
           'an envelope starts as a draft', env.status)
        ok(not env.is_open, '  and a draft is not open for signature')

        # THE UPLOAD PATH BOUNDS THE SLUG.
        ok(len(os.path.basename(env.original_pdf.name)) < 100,
           '  and its filename is bounded, so nothing truncates it',
           env.original_pdf.name)

        party = LeaseSigningParty.objects.create(
            signing=env, role=LeaseSigningParty.ROLE_TENANT, order=1,
            name='Andreas Georgiou', email='a.georgiou@example.com')

        raw = party.issue_token()
        party.save()

        ok(len(raw) >= 40,
           'a minted token is long enough to be unguessable', len(raw))
        ok(party.token_hash and len(party.token_hash) == 64,
           '  and what is STORED is a 64-character hash',
           party.token_hash[:16] + '...')

        # THE RAW TOKEN CANNOT BE RECOVERED FROM THE ROW. Asked of
        # every field, not of the one we expect - a credential that
        # leaks into some other column is still leaked.
        fresh = LeaseSigningParty.objects.get(pk=party.pk)
        every = ' '.join(str(getattr(fresh, f.name, '') or '')
                         for f in fresh._meta.fields)
        ok(raw not in every,
           'THE RAW TOKEN IS NOWHERE IN THE ROW - not in any field',
           [f.name for f in fresh._meta.fields
            if raw in str(getattr(fresh, f.name, '') or '')])

        # AND THE LOOKUP WORKS BY HASHING THE CANDIDATE.
        found = LeaseSigningParty.objects.filter(
            token_hash=LeaseSigningParty.hash_token(raw)).first()
        ok(found and found.pk == party.pk,
           '  and a holder of the link is found by hashing what they '
           'present', found)
        ok(not LeaseSigningParty.objects.filter(
               token_hash=LeaseSigningParty.hash_token(raw + 'x')).first(),
           '  while one character wrong finds nobody')

        # A RESEND MINTS A NEW ONE AND KILLS THE OLD LINK.
        again = party.issue_token()
        party.save()
        ok(again != raw, 'a resend mints a DIFFERENT token', )
        ok(not LeaseSigningParty.objects.filter(
               token_hash=LeaseSigningParty.hash_token(raw)).first(),
           '  and the OLD link stops working - a link that expires and '
           'then works again never really expired')

        # TWO STRENGTHS OF EVIDENCE, AND THE TRAIL KEEPS THEM APART.
        #
        # Decided 23 October. A tenant can only ever be a link holder.
        # The Alivente signer, when it is the person who created the
        # envelope, goes straight to the page already authenticated -
        # and the trail can then say WHO rather than only that a link
        # was held. Levelling that down to the weaker fact would throw
        # away evidence for no reason.
        party.signed_auth = LeaseSigningParty.AUTH_TOKEN
        party.save(update_fields=['signed_auth'])
        ok(LeaseSigningParty.objects.get(pk=party.pk).signed_auth
           == 'token', 'a tenant signature records LINK HOLDER')

        mine = LeaseSigningParty.objects.create(
            signing=env, role=LeaseSigningParty.ROLE_ALIVENTE, order=0,
            name='Demetri Manias', email='demetri@example.com',
            signed_auth=LeaseSigningParty.AUTH_SESSION,
            signed_by_user=me, signed_at=timezone.now())
        back = LeaseSigningParty.objects.get(pk=mine.pk)
        ok(back.signed_auth == 'session' and back.signed_by_user_id == me.pk,
           '  while an Alivente signature records WHO was signed in',
           '%s / %s' % (back.signed_auth, back.signed_by_user))
        ok(back.order < party.order,
           '  and Alivente is order 0, so it signs first')

        # ==============================================================
        head('4. DRIVEN - the trail, which is the evidence')
        # ==============================================================
        now = timezone.now()
        for kind in ('created', 'sent', 'viewed', 'signed'):
            LeaseSigningEvent.objects.create(
                signing=env,
                party=party if kind in ('viewed', 'signed') else None,
                kind=kind, ip='198.51.100.7', user_agent='Safari/iPhone')

        trail = list(env.events.all())
        ok([e.kind for e in trail] == ['created', 'sent', 'viewed',
                                       'signed'],
           'the trail reads back in the order it happened',
           [e.kind for e in trail])
        ok(trail[0].party is None and trail[2].party_id == party.pk,
           '  an envelope event has no party; a person event does - '
           'inventing one would make the trail say something untrue')
        ok(all(e.ip for e in trail),
           '  and every row carries where it came from')

        # DELETING A PARTY MUST NOT ERASE WHAT THEY DID.
        party.delete()
        after = list(env.events.all())
        ok(len(after) == 4,
           'DELETING A PARTY LEAVES THE TRAIL STANDING - the evidence '
           'does not depend on the person still existing',
           len(after))
        ok(all(e.party_id is None for e in after),
           '  with their rows orphaned rather than removed')

        # AND DELETING THE ENVELOPE TAKES ITS OWN EVENTS WITH IT.
        env_id = env.pk
        LeaseSigningParty.objects.filter(signing=env).delete()
        env.delete()
        ok(not LeaseSigningEvent.objects.filter(signing_id=env_id).exists(),
           'and deleting the ENVELOPE takes its events - a trail with '
           'nothing to be about is not evidence, it is litter')

        # THE TENANT SURVIVES. PROTECT, because losing a lease envelope
        # must never be a way to lose a tenant.
        ok(Tenant.objects.filter(pk=t.pk).exists(),
           'and the tenant is untouched throughout')
    except Exception as exc:
        ok(False, 'sections 3 and 4 ran to the end', repr(exc)[:300])


# ==========================================================================
head('5. THE MIGRATION')
# ==========================================================================
ok(os.path.isfile(MIG), 'the round brings its own migration', MIG)
if os.path.isfile(MIG):
    g = read(MIG)
    ok(g.count('migrations.CreateModel') == 3,
       '  three CreateModel, one per table',
       g.count('migrations.CreateModel'))
    ok(not any(b in g for b in ('RunPython', 'RunSQL', 'DeleteModel',
                                'RemoveField', 'AlterField')),
       '  and it touches nothing that already exists')
    names = sorted(n[:-3] for n in
                   os.listdir(os.path.join(ROOT, 'pages', 'migrations'))
                   if n.endswith('.py') and n != '__init__.py'
                   and '.bak_' not in n and 'es1_lease_signing' not in n)
    ok(names and ("'%s'" % names[-1]) in g.replace('"', "'"),
       '  depending on the migration that really is latest',
       'latest on disk: %s' % (names[-1] if names else '(none)'))


# ==========================================================================
head('6. REGISTRATION')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1, '  exactly once')
ok('def issue_token' in gate, 'and a sentinel watches the token')
ok('class LeaseSigningEvent' in gate, 'and one watches the trail')

print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that anything can be signed. There is no view, no route,')
print('  no screen and no email - deliberately. This is the shape of')
print('  the data; ES-2 upward is the behaviour.')
print('')
print('  Not that the token is delivered safely. It goes in an email,')
print('  and an email is not a secure channel. That is the accepted')
print('  cost of a link with no login, taken on 23 October with the')
print('  guards named: one envelope, seven days, dead on cancel, and')
print('  every view and signature recorded.')
print('')
print('  Not that two tenants is enforced. The model permits any')
print('  number of parties; the LIMIT of one Alivente and two tenants')
print('  belongs to the screen that creates them, which is ES-3.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
