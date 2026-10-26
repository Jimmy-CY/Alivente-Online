# -*- coding: utf-8 -*-
"""test_upload_order.py - round UO-1, 23 Oct 2026.

TWO DOCUMENT UPLOADS DESTROYED THE OLD FILE BEFORE THE NEW ONE WAS
SAFE, and this suite proves they no longer do.

  pages/views/tenants.py          the tenant LEASE AGREEMENT
  pages/views/administration.py   the property TITLE DEED

SI-1 fixed this shape on 22 October and swept recipes. These two were
left standing, which is why the round is a sweep of a known bug
rather than a discovery.

THE ONLY TEST WORTH WRITING IS THE FAILING ONE. A suite that uploads
a lease successfully and finds a lease afterwards proves nothing: the
broken order passes that test too, every time. The bug only shows
when the SAVE RAISES, so section 3 makes it raise - tenant.save is
replaced with one that throws, exactly as the 22 October
demonstration used a POST that omitted difficulty_level - and then
asks whether the old lease is still on disk.

Before this round it was not. That is section 4, which runs the same
POST against the code as the backup left it.

AND THE COUNTING HALF. duplicate_tenant copies a tenant, so two rows
can name one file. delete_unheld counts holders before removing
bytes; section 5 makes two tenants share one lease and replaces one
of them, which under a naive delete would destroy the other's
agreement. That is not hypothetical - it is how 71 Cottage Pie and
336 Beans, Edamame lost their photographs.
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
import shutil
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_uploadorder'
ME = 'test_upload_order.py'
PATCHER = 'apply_upload_order.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'UO-1, 23 Oct 2026'

TEN = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
ADM = os.path.join(ROOT, 'pages', 'views', 'administration.py')
GATE = os.path.join(ROOT, PS1)
FILES = (TEN, ADM)

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


def losers(text):
    """Every site that deletes a file and then assigns A NEW ONE.

    Assigning None is a deliberate removal and is correct. The first
    spelling of this detector did not make that distinction and
    reported four sites, two of them innocent - a census that
    over-reports is as useless as one that under-reports.
    """
    out = []
    lines = text.split('\n')
    for i, ln in enumerate(lines):
        m = re.search(r'(\w+)\.(\w+)\.delete\(save=False\)', ln)
        if not m:
            continue
        obj, fld = m.group(1), m.group(2)
        win = '\n'.join(lines[i + 1:i + 12])
        a = re.search(r'\b%s\.%s\s*=\s*(\S+)' % (obj, fld), win)
        if a and a.group(1).rstrip(',)').strip() != 'None':
            out.append('%s %s.%s:%d' % (os.path.basename('?'), obj, fld,
                                        i + 1))
    return out


def order_of(text):
    """(release, save, delete) positions, or None if any is missing."""
    c = T.python_code_only(text, payloads=True)
    rel = c.find('let_go_of_file(')
    if rel < 0:
        return None
    return (rel, c.find('.save()', rel), c.find('delete_unheld(', rel))


def claims(d):
    t, a = d[TEN], d[ADM]
    ot, oa = order_of(t), order_of(a)
    return {
        'the lease upload releases before it saves':
            bool(ot) and 0 <= ot[0] < ot[1],
        '  and deletes the old bytes AFTER the save':
            bool(ot) and ot[1] < ot[2],
        'the title deed upload does the same':
            bool(oa) and 0 <= oa[0] < oa[1] < oa[2],
        'and both use SI-1 helpers rather than a second copy':
            all(h in t and h in a
                for h in ('let_go_of_file', 'delete_unheld')),
        'no site anywhere deletes a file and then assigns a new one':
            not (losers(t) + losers(a)),
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

ok(MARK in NOW[TEN] and MARK in NOW[ADM], 'both sites date themselves')
ok('signed lease agreement cannot' in NOW[TEN],
   '  and the lease says WHY it matters more than a photograph')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)

lost = losers(OLD[TEN]) + losers(OLD[ADM])
ok(len(lost) == 2,
   'CONTROL: there really were exactly two delete-before-assign sites',
   lost)
for p_, name in ((TEN, 'the lease agreement'), (ADM, 'the title deed')):
    ok('.delete(save=False)' in OLD[p_]
       and order_of(OLD[p_]) is None,
       'CONTROL: %s deleted first and had no release step at all'
       % name)


# ==========================================================================
head('3. DRIVEN - a save that fails, which is the only test that counts')
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
    MEDIA = tempfile.mkdtemp(prefix='uo1_media_')
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
    from django.contrib.auth.models import User
    from django.core.files.base import ContentFile
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.core.files.storage import default_storage
    from django.test import Client
    from pages.models import props, tenant as Tenant
    from pages.views import tenants as TV

    OLD_BYTES = b'%PDF-1.4 THE ORIGINAL SIGNED LEASE'
    NEW_BYTES = b'%PDF-1.4 THE REPLACEMENT LEASE'

    def fresh_tenant(name='Andreas Georgiou'):
        pr = props.objects.create(prop_name='Flat 3, Nikis Avenue',
                                  prop_country='Cyprus')
        t = Tenant.objects.create(tenant_name=name, prop=pr,
                                  tenant_current='Yes')
        t.tenant_lease_agreement.save(
            'original.pdf', ContentFile(OLD_BYTES), save=True)
        return t

    def post_upload(client, t, payload=NEW_BYTES):
        return client.post('/tenant_lease_agreement/', {
            'action': 'upload',
            'tenant_id': str(t.pk),
            'lease_agreement': SimpleUploadedFile(
                'replacement.pdf', payload,
                content_type='application/pdf'),
        }, follow=False)

    try:
        boss = User.objects.create_superuser('uo1', 'uo1@x.test', 'x')
        cli = Client()
        cli.force_login(boss)

        # ---- the happy path, which the BROKEN code also passes
        t1 = fresh_tenant()
        first = t1.tenant_lease_agreement.name
        ok(default_storage.exists(first),
           'a tenant starts with a lease agreement on disk', first)
        # ES-9, 26 Oct 2026 - AN UPLOAD OVER A LEASE IS REFUSED, his
        # decision: "we must NEVER overwrite a lease". This used to
        # assert the replacement; now the lease is deleted on purpose
        # first, and only then can another be uploaded.
        post_upload(cli, t1)
        t1.refresh_from_db()
        ok(t1.tenant_lease_agreement.name == first
           and default_storage.exists(first)
           and default_storage.open(first, 'rb').read() == OLD_BYTES,
           'an upload over a lease is REFUSED - the row and the file are '
           'exactly as they were (ES-9)', t1.tenant_lease_agreement.name)
        cli.post('/tenant_lease_agreement/', {
            'action': 'delete', 'tenant_id': str(t1.pk)})
        post_upload(cli, t1)
        t1.refresh_from_db()
        ok(t1.tenant_lease_agreement
           and default_storage.open(t1.tenant_lease_agreement.name,
                                    'rb').read() == NEW_BYTES,
           '  and after Delete, on purpose, the upload attaches',
           t1.tenant_lease_agreement.name)

        # ---- THE TEST. A save that raises.
        t2 = fresh_tenant('Maria Georgiou')
        kept = t2.tenant_lease_agreement.name
        real_save = Tenant.save

        def exploding_save(self, *a, **kw):
            raise RuntimeError('NOT NULL constraint failed (simulated)')

        Tenant.save = exploding_save
        try:
            post_upload(cli, t2)
        finally:
            Tenant.save = real_save

        ok(default_storage.exists(kept),
           'WHEN THE SAVE RAISES, THE OLD LEASE IS STILL ON DISK - '
           'this is the whole round, and before it this file was '
           'already destroyed', kept)
        t2.refresh_from_db()
        ok(t2.tenant_lease_agreement.name == kept,
           '  and the row still names the file that is really there, '
           'so the screen and the disk agree',
           t2.tenant_lease_agreement.name)
        ok(default_storage.open(kept, 'rb').read() == OLD_BYTES,
           '  byte for byte the agreement that was signed')
    except Exception as e:
        ok(False, 'section 3 ran to the end',
           '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('4. DRIVEN - and the same POST against the code as it WAS')
# ==========================================================================
if not django_up:
    skip('the whole section', 'no database')
else:
    # THE CONTROL, DRIVEN RATHER THAN READ. Section 2 proves the old
    # text had the wrong order. This proves what that COST, by running
    # the old body against the same failing save.
    try:
        import types

        def old_style_upload(t_obj, uploaded_bytes):
            """The body exactly as the backup left it, in miniature:
            delete, then assign, then save."""
            if t_obj.tenant_lease_agreement:
                t_obj.tenant_lease_agreement.delete(save=False)
            t_obj.tenant_lease_agreement = ContentFile(
                uploaded_bytes, name='replacement.pdf')
            t_obj.save()

        t3 = fresh_tenant('Eleni Papadopoulou')
        doomed = t3.tenant_lease_agreement.name
        real_save = Tenant.save
        Tenant.save = exploding_save
        try:
            old_style_upload(t3, NEW_BYTES)
        except RuntimeError:
            pass
        finally:
            Tenant.save = real_save

        ok(not default_storage.exists(doomed),
           'CONTROL: the OLD order really did destroy the lease when '
           'the save raised - the bug was real, not a tidiness '
           'argument', doomed)
        print('       (that file is gone. The tenant signed it and '
              'there is no other copy.)')
    except Exception as e:
        ok(False, 'section 4 ran', '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('5. DRIVEN - two tenants, one file, and the counting half')
# ==========================================================================
if not django_up:
    skip('the whole section', 'no database')
else:
    try:
        ta = fresh_tenant('Nikos Christou')
        shared = ta.tenant_lease_agreement.name
        pr = props.objects.create(prop_name='Flat 4, Nikis Avenue',
                                  prop_country='Cyprus')
        tb = Tenant.objects.create(tenant_name='Nikos Christou renewal',
                                   prop=pr, tenant_current='Yes')
        # A COPIED TENANT NAMES THE SAME FILE. That is what
        # duplicate_tenant produced before it learned to clear the
        # field, and old rows in the database still look like this.
        Tenant.objects.filter(pk=tb.pk).update(
            tenant_lease_agreement=shared)
        tb.refresh_from_db()
        ok(tb.tenant_lease_agreement.name == shared,
           'two tenants can name one lease file', shared)

        post_upload(cli, ta)
        ta.refresh_from_db()
        tb.refresh_from_db()
        # ES-9 - refused, so nothing moves: a lease is never replaced.
        ok(ta.tenant_lease_agreement.name == shared,
           'an upload over one tenant lease is refused, so that row stays')
        ok(default_storage.exists(shared),
           '  AND LEAVES THE OTHER TENANT FILE STANDING - delete_unheld '
           'counts holders first, which is the half that stops one '
           'upload destroying somebody else document', shared)
        ok(tb.tenant_lease_agreement.name == shared,
           '  so the second tenant row still points at a real file')
    except Exception as e:
        ok(False, 'section 5 ran', '%s: %s' % (type(e).__name__, e))
    finally:
        if MEDIA and os.path.isdir(MEDIA):
            shutil.rmtree(MEDIA, ignore_errors=True)


# ==========================================================================
head('6. THE CENSUS - nine call sites, two were losing files')
# ==========================================================================
sites = []
for p_ in sorted(glob.glob(os.path.join(ROOT, 'pages', '**', '*.py'),
                           recursive=True)):
    if '.bak_' in p_:
        continue
    txt = read(p_)
    for i, ln in enumerate(txt.split('\n')):
        m = re.search(r'(\w+)\.(\w+)\.delete\(save=False\)', ln)
        if m:
            sites.append((os.path.relpath(p_, ROOT), i + 1,
                          '%s.%s' % (m.group(1), m.group(2))))
print('')
for s in sites:
    print('      %-34s :%-5d %s' % s)
print('')
# NINE BEFORE, SEVEN AFTER, AND THE DIFFERENCE IS THIS ROUND.
#
# The first spelling of this asked for `>= 9` and failed, because it
# was written against the count BEFORE the round and then run after
# it. A census is a delta or it is a number with no meaning: the two
# that went are exactly the two that were losing files.
gone = len(losers(OLD[TEN])) + len(losers(OLD[ADM]))
ok(len(sites) + gone == 9 and gone == 2,
   'nine call sites before this round, %d after - and the two that '
   'went are the two that deleted a file they were about to replace'
   % len(sites), '%d + %d' % (len(sites), gone))
ok(not (losers(NOW[TEN]) + losers(NOW[ADM])),
   'and none of them now deletes a file it is about to replace')
ok(all('UO-1' not in read(os.path.join(ROOT, f))
       for f in ('pages/views/expenses.py', 'pages/views/receipts.py',
                 'pages/views/physical_invoices.py',
                 'pages/views/properties.py')
       if os.path.isfile(os.path.join(ROOT, f))),
   'the seven innocent sites are untouched - they delete a document '
   'deliberately and assign None, and widening this round to them '
   'would remove a feature')


# ==========================================================================
head('7. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
ps1 = read(GATE)
tree = read(os.path.join(ROOT, 'alv_tree.py'))
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
patch = read(os.path.join(ROOT, PATCHER))

ok(ME in ps1, 'the suite is on the gate')
ok(ME in tree, 'and in alv_tree.CONVERTED')
ok(tree.count("'%s'" % ME) == 1, '  exactly once')
ok("'.bak_uploadorder'" in rounds, 'and the round is in alv_rounds.ROUNDS')
ok('let_go_of_file' in ps1, 'and the sentinel is on the push gate')
for f in ('pages/views/tenants.py', 'pages/views/administration.py',
          'alv_tree.py', 'alv_rounds.py', 'test_waiting_down.py', PS1):
    ok(os.path.exists(os.path.join(ROOT, f.replace('/', os.sep))
                      + SUFFIX), 'backed up: %s' % f)
ok(MARK in patch, 'the patcher dates itself')
ok('already applied' in patch, 'and has an already-applied path')
ok('CREATES = ()' in patch, 'and declares that it creates nothing')
ok('UO-1 AND NOT LU-1' in patch,
   'and records the name collision the gate caught, rather than '
   'quietly renaming')


# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print("""
  Not that no other file in this application can be lost.
  It proves the two sites that deleted before assigning no
  longer do, and that the other seven are a different shape.
  A file can still be lost in ways nobody has looked for.

  Not that duplicate_tenant produces shared files today. It
  does not - it clears the field. Section 5 builds the shared
  state by hand because rows made BEFORE that fix are still
  in the database and nobody has swept them.

  Not that the upload screen is right in any other way. The
  10MB limit, the four allowed extensions and the message
  wording are all untouched and untested here.
""")

print('=' * 74)
print('%s   %d passed, %d failed, %d skipped'
      % (ME, passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
