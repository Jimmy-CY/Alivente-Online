# -*- coding: utf-8 -*-
"""test_lease_signing.py - round ES-3a, 23 Oct 2026.

THE ENVELOPE REGISTER, AND THE FOURTH TILE THAT REACHES IT.

Read only. Section 4 drives a tenant with TWO envelopes - one expired,
one live - through the real view and asks for two rows, because that
is the entire argument for a screen of its own. Manage Lease
Agreements is one row per tenant and has to be; a tenant with two
attempts can only appear once there, and the one it shows would be
arbitrary.

AND SECTION 5 ASKS WHETHER LOOKING CHANGED ANYTHING. A register that
quietly expired rows as a side effect of being read is a register
nobody can reason about, so the suite counts the database before and
after a request and compares every field it could have touched.

WHAT IS DELIBERATELY NOT HERE. Nothing creates an envelope, sends
one, or signs one - that is ES-3b and ES-4. This round lists what
ES-1 can already hold.
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

SUFFIX = '.bak_leasesigning'
ME = 'test_lease_signing.py'
PATCHER = 'apply_lease_signing.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-3a, 23 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'lease_signing.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'lease_signing_list.html')
ADMIN = os.path.join(ROOT, 'pages', 'templates', 'admin_apms.html')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
INIT = os.path.join(ROOT, 'pages', 'views', '__init__.py')
GATE = os.path.join(ROOT, PS1)
FILES = (ADMIN, URLS, INIT)

GREEK = 'Ανδρέας Γεωργίου'

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


def claims(d):
    return {
        'the fourth tile is in the FUNCTIONAL panel':
            'Manage Lease Signing' in d[ADMIN],
        '  and reaches the register':
            "{% url 'lease_signing_list' %}" in d[ADMIN],
        '  behind the same permission as the two lease tiles beside it':
            'fa-file-signature' in d[ADMIN]
            and 'can_access_tenants' in d[ADMIN],
        'the route is registered':
            "name='lease_signing_list'" in d[URLS],
        'and the view module is re-exported':
            'from .lease_signing import *' in d[INIT],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

v = T.python_code_only(read(VIEW), payloads=True)
ok('__all__' in v and '"lease_signing_list"' in v,
   'the view is in __all__ - `import *` obeys it, so a view missing '
   'from that list does not exist to the URLconf however correct it is')
ok("permission_required('auth.can_access_tenants'" in v,
   '  and requires what the tile promises')

# READ ONLY, ASSERTED IN THE SOURCE AS WELL AS DRIVEN IN SECTION 5.
writes = [w for w in ('.save(', '.delete(', '.update(', '.create(')
          if w in v]
ok(not writes,
   'the view writes nothing - expiring a row as a side effect of '
   'listing it would belong to ES-5, not here', writes)

t = read(TPL)
ok('{% block title %}' in t,
   'the template has a title block - test_heading_prefix reported '
   'exactly this against RV-1 the day before, 1 of 116 bad')
ok(t.count('data-label=') >= 5,
   '  and labels its cells, so BASE turns rows into cards below 768px '
   'rather than this page drawing a ninth hand-written set',
   t.count('data-label='))
ok(not re.search(r'@media\s*\(\s*max-width', T.code_only(t)),
   '  and its media query is `screen and`, so the phone layout cannot '
   'leak onto paper')
ok('mobile-action-bar' in t,
   '  with the house phone action bar, not a hand-rolled one')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v_ in claims(OLD).items() if v_]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)
ok(not os.path.exists(VIEW + SUFFIX)
   and not os.path.exists(TPL + SUFFIX),
   'CONTROL: neither the view nor the template has a backup, because '
   'this round creates them rather than editing something that was here')

# AND THE PANEL REALLY HAD THREE TILES.
seg_old = OLD[ADMIN]
a_ = seg_old.find('id="panel-functional"')
b_ = seg_old.find('id="panel-system"')
ok(seg_old[a_:b_].count('<h6>') == 6,
   'CONTROL: the functional panel drew three tiles - six <h6>, a '
   'permitted and a refused arm each - and the fourth cell was empty',
   seg_old[a_:b_].count('<h6>'))


# ==========================================================================
head('3. DRIVEN - Django can build the URLconf at all')
# ==========================================================================
django_up = False
MEDIA = None
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
    MEDIA = tempfile.mkdtemp(prefix='es3a_media_')
    dj.MEDIA_ROOT = MEDIA
    from django.core.files.storage import default_storage
    for _a in ('base_location', 'location'):
        default_storage.__dict__.pop(_a, None)
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
    skip('sections 3, 4 and 5', 'no database')
else:
    from django.urls import reverse, NoReverseMatch
    try:
        url = reverse('lease_signing_list')
        ok(url == '/lease-signing/',
           'the route reverses - which is the claim __all__ gates, and '
           'the one RV-1 got wrong on 23 October', url)
    except NoReverseMatch as e:
        ok(False, 'the route reverses', str(e))


# ==========================================================================
head('4. DRIVEN - one tenant, two envelopes, two rows')
# ==========================================================================
if not django_up:
    skip('the whole section', 'no database')
else:
    from django.contrib.auth.models import User
    from django.core.files.base import ContentFile
    from django.test import Client
    from django.utils import timezone
    import datetime as dt
    from pages.models import (LeaseSigning, LeaseSigningParty,
                              props, tenant as Tenant)

    try:
        boss = User.objects.create_superuser('es3a', 'es3a@x.test', 'x')
        pr = props.objects.create(prop_name='Flat 3, Nikis Avenue',
                                  prop_country='Cyprus')
        tn = Tenant.objects.create(tenant_name=GREEK, prop=pr,
                                   tenant_current='Yes')

        def envelope(status, days, signed_n):
            e = LeaseSigning.objects.create(
                tenant=tn, created_by=boss, status=status,
                sent_at=timezone.now() - dt.timedelta(days=9 - days),
                expires_at=timezone.now() + dt.timedelta(days=days))
            e.original_pdf.save('lease.pdf', ContentFile(b'%PDF-1.4 x'),
                                save=True)
            for i, (role, name) in enumerate((
                    (LeaseSigningParty.ROLE_ALIVENTE, 'Demetri Manias'),
                    (LeaseSigningParty.ROLE_TENANT, GREEK))):
                LeaseSigningParty.objects.create(
                    signing=e, role=role, order=i, name=name,
                    signed_at=(timezone.now() if i < signed_n else None))
            return e

        dead = envelope(LeaseSigning.EXPIRED, -4, 1)
        live = envelope(LeaseSigning.PART, 6, 1)

        cli = Client()
        cli.force_login(boss)
        r = cli.get('/lease-signing/')
        ok(r.status_code == 200, 'the register renders', r.status_code)
        rows = r.context['rows']
        ok(len(rows) == 1,
           'live only by default - the expired attempt is not shown',
           [x['env'].pk for x in rows])

        r2 = cli.get('/lease-signing/?all=1')
        rows2 = r2.context['rows']
        ok(len(rows2) == 2,
           'INCLUDE FINISHED SHOWS BOTH ATTEMPTS BY ONE TENANT - which '
           'is the whole argument for a screen of its own, because '
           'Manage Lease Agreements could only ever show one of them',
           [x['env'].pk for x in rows2])
        ok(len(set(x['tenant'].pk for x in rows2)) == 1,
           '  and they really are the same tenant')

        body = r2.content.decode('utf-8')
        ok(GREEK in body,
           '  with the tenant name in Greek, drawn by the template')
        ok(body.count('ls-dot') >= 4,
           '  and a signer dot per party on each row', body.count('ls-dot'))

        one = [x for x in rows2 if x['env'].pk == live.pk][0]
        ok(one['signed'] == 1 and one['total'] == 2,
           'the live envelope reads 1 of 2',
           '%s of %s' % (one['signed'], one['total']))
        ok([m['state'] for m in one['marks']] == ['done', 'wait'],
           '  and Alivente is the FIRST dot, because Alivente signs '
           'first', [m['state'] for m in one['marks']])

        gone = [x for x in rows2 if x['env'].pk == dead.pk][0]
        ok(gone['status_pill'] == 'alv-pill-neutral',
           'an expired attempt is neutral, not alarming - it is history')
    except Exception as e:
        ok(False, 'section 4 ran to the end',
           '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('5. DRIVEN - and looking at it changed nothing')
# ==========================================================================
if not django_up:
    skip('the whole section', 'no database')
else:
    try:
        FIELDS = ('status', 'sent_at', 'expires_at', 'completed_at',
                  'last_reminder_at', 'cancelled_at', 'pdf_sha256')

        def snapshot():
            return sorted(
                (e.pk, tuple(str(getattr(e, f)) for f in FIELDS))
                for e in LeaseSigning.objects.all())

        before = snapshot()
        n_before = (LeaseSigning.objects.count(),
                    LeaseSigningParty.objects.count())
        cli.get('/lease-signing/')
        cli.get('/lease-signing/?all=1')
        after = snapshot()
        n_after = (LeaseSigning.objects.count(),
                   LeaseSigningParty.objects.count())

        ok(before == after,
           'TWO REQUESTS AND NOT ONE FIELD MOVED - an expired row is '
           'READ as expired and never written, because a list view that '
           'mutates as a side effect of being looked at is one nobody '
           'can reason about',
           [b for b, a in zip(before, after) if b != a][:2])
        ok(n_before == n_after,
           '  and nothing was created or deleted either',
           '%s then %s' % (n_before, n_after))

        # AND THE COMPARISON CAN FAIL. A check that cannot is not one.
        dead.status = LeaseSigning.CANCELLED
        dead.save()
        ok(snapshot() != before,
           'CONTROL: the snapshot NOTICES a change, so the two above '
           'are checks and not decoration')
    except Exception as e:
        ok(False, 'section 5 ran', '%s: %s' % (type(e).__name__, e))
    finally:
        if MEDIA and os.path.isdir(MEDIA):
            shutil.rmtree(MEDIA, ignore_errors=True)


# ==========================================================================
head('6. THE NINETEEN CENSUS MOVES')
# ==========================================================================
# WHAT ONE NEW TEMPLATE COSTS IN THIS TREE, named rather than
# discovered. RV-1 moved eleven for one screen the day before; this
# round moved nineteen and found every one of them by running the
# suites BEFORE delivery rather than by a push being refused.
MOVED = ('test_house_title.py', 'test_bar_height.py', 'test_help_label.py',
         'test_tree_roots.py', 'test_js_buttons.py', 'test_recipe_side_b.py',
         'test_subtree_tones.py', 'test_recipe_tones.py',
         'test_landing_tab.py')
patch = read(os.path.join(ROOT, PATCHER))
for n in MOVED:
    ok(n in patch and os.path.exists(os.path.join(ROOT, n) + SUFFIX),
       'moved and backed up: %s' % n)
ok(MARK in read(os.path.join(ROOT, 'pages', 'templates', 'base.html')),
   "and base.html's own house-title note moved with the count it "
   'states - RV-1 found that note three days out of date')

# TWO OF THEM WERE REPAIRS, NOT BUMPS.
ok('which drifted with every later round' in patch,
   'two claims in test_landing_tab were REPAIRED rather than bumped - '
   'they tied a historical control to a live census, so they broke for '
   'every future round and not just this one')
ok('CREATED_LATER' in patch,
   'and a page created after a round cannot be in that round past, '
   'which is a named exclusion rather than a loosened count')


# ==========================================================================
head('7. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
g = read(GATE)
tree = read(os.path.join(ROOT, 'alv_tree.py'))
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))

ok(ME in g, 'the suite is on the gate')
ok(ME in tree, 'and in alv_tree.CONVERTED')
ok(tree.count("'%s'" % ME) == 1, '  exactly once')
ok("'.bak_leasesigning'" in rounds, 'and the round is in alv_rounds.ROUNDS')
ok('ONE ROW PER ENVELOPE' in g, 'and the sentinel is on the push gate')
for f in ('pages/templates/admin_apms.html', 'pages/urls.py',
          'pages/views/__init__.py'):
    ok(os.path.exists(os.path.join(ROOT, f.replace('/', os.sep)) + SUFFIX),
       'backed up: %s' % f)
ok(MARK in patch, 'the patcher dates itself')
ok('already applied' in patch, 'and has an already-applied path')
ok('CREATES = (VIEW, TPL)' in patch, 'and declares the two it creates')


# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print("""
  Not that the register looks right. It proves what it SAYS -
  the rows, the counts, the dots, the pills. Whether it looks
  like an Alivente screen is a render Demetri has to see, and
  he has seen one; this is not that.

  Not that the eye, resend and cancel controls do anything.
  They are drawn and they are inert. ES-3b builds what they
  point at, and a control that looks live and is not is worth
  naming rather than leaving to be discovered.

  Not that an envelope can be created. Nothing in this round
  makes one - section 4 builds them through the ORM. The
  screen that sends a lease is ES-3b.

  Not that expiry happens. The register READS a past date as
  expired and writes nothing. Whatever moves a row into the
  EXPIRED status is ES-5, and until then nothing does.
""")

print('=' * 74)
print('%s   %d passed, %d failed, %d skipped'
      % (ME, passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
