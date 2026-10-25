# -*- coding: utf-8 -*-
"""test_envelope_delete.py - round ES-7b, 25 Oct 2026.

DELETING AN ENVELOPE - WITH THE CHECKS AND BALANCES - DRIVEN.

His decisions of 25 October: any envelope that is no longer live may be
deleted (signed ones too, with a warning that the signatures are the
evidence); superuser only; and no trace is kept.

THE CLAIMS WITH TEETH: a live envelope cannot be deleted, a mistyped
number deletes nothing, someone who is not a superuser deletes nothing -
and the FILES go only after the rows have, so a failed delete costs
nothing (UO-1's order).
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
import shutil
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_envdelete'
ME = 'test_envelope_delete.py'
PATCHER = 'apply_envelope_delete.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-7b, 25 Oct 2026'

J = os.path.join
VIEW = J(ROOT, 'pages', 'views', 'lease_signing_approve.py')
URLS = J(ROOT, 'pages', 'urls.py')
PAGE = J(ROOT, 'pages', 'templates', 'lease_signing_detail.html')
GATE = J(ROOT, PS1)
EDITED = (VIEW, URLS, PAGE)

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

NOW = dict((p, read(p)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def claims(src):
    v = T.python_code_only(src[VIEW])
    u = T.python_code_only(src[URLS])
    pg = T.code_only(src[PAGE])
    return [
        ('def lease_signing_delete(request, pk):' in v
         and '@user_passes_test(lambda u: u.is_superuser)' in v,
         'an envelope can be deleted - by a superuser only'),
        ('DELETABLE = (LeaseSigning.CANCELLED, LeaseSigning.EXPIRED,' in v
         and 'if env.status not in DELETABLE:' in v,
         '  never while it is live'),
        ("!= str(env.pk):" in v,
         '  and only when the number is typed back'),
        ('transaction.on_commit(_remove_files)' in v,
         '  and its files go only AFTER the rows have'),
        ("name='lease_signing_delete'" in u
         and "{% url 'lease_signing_delete' env.pk %}" in pg
         and '{% if can_delete %}' in pg,
         'the envelope page carries the control, only when allowed'),
        ('This envelope holds {{ signed_count }} signature' in pg,
         'and WARNS when there are signatures to destroy'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
ok(all(MARK in NOW[p] for p in EDITED),
   'the round dates itself in every file it touched')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))


# ==========================================================================
# DRIVEN
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
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    from django.db import connection, transaction
    from django.test import Client
    from django.test.utils import override_settings
    from django.utils import timezone
    import pages.models as M
    from pages.services import lease_sealing as LS
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('section 3', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


class Rollback(Exception):
    """Nothing this suite writes survives it."""


have_db = False
if django_up:
    try:
        connection.ensure_connection()
        M.LeaseSigning.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])


def a_pdf():
    import pymupdf
    doc = pymupdf.open()
    for n in range(2):
        doc.new_page(width=595, height=842).insert_text(
            (72, 110), 'LEASE page %d' % (n + 1), fontsize=14)
    raw = doc.tobytes()
    doc.close()
    return raw


def run_on_commit():
    """Fire what the view queued for after-commit, inside our rollback."""
    queued = list(connection.run_on_commit)
    connection.run_on_commit[:] = []
    for item in queued:
        item[1]()


if have_db:
    import datetime as dt
    head('3. DRIVEN - who, when, and what it takes with it')
    tmp = tempfile.mkdtemp(prefix='alv_es7b_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        with transaction.atomic():
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(Permission)
            boss = User.objects.create_superuser(
                'es7bboss', 'es7b.boss@example.com', 'not-a-real-password')
            staff = User.objects.create_user(
                'es7bstaff', 'es7b.staff@example.com', 'not-a-real-password')
            for code in ('can_edit_tenants', 'can_access_tenants'):
                staff.user_permissions.add(Permission.objects.get_or_create(
                    codename=code,
                    defaults={'name': code, 'content_type': ct})[0])
            c = Client(SERVER_NAME='localhost')
            c.force_login(boss)
            s = Client(SERVER_NAME='localhost')
            s.force_login(staff)
            prop = M.props.objects.create(prop_name='Flat 9', prop_country='Cyprus')
            ten = M.tenant.objects.create(
                prop=prop, tenant_type='Individual',
                tenant_name='Ms. Anastasia Test', tenant_email='a.test@example.com',
                tenant_lease_start_date=dt.date(2026, 12, 1),
                tenant_lease_end_date=dt.date(2027, 11, 30), tenant_current='Yes')

            def envelope(status, signed=0):
                e = M.LeaseSigning.objects.create(
                    tenant=ten, source=M.LeaseSigning.SOURCE_UPLOADED,
                    status=status, created_by=boss,
                    expires_at=timezone.now() + dt.timedelta(days=3))
                e.original_pdf.save('lease.pdf', ContentFile(a_pdf()), save=True)
                e.page_count = LS.render_pages(e)
                e.save(update_fields=['page_count'])
                for i in range(2):
                    M.LeaseSigningParty.objects.create(
                        signing=e, role='alivente' if i == 0 else 'tenant',
                        order=i, name='Signer %d' % i, email='s%d@example.com' % i,
                        signed_at=timezone.now() if i < signed else None)
                M.LeaseSigningEvent.objects.create(signing=e, kind='created')
                return e

            # ---- A LIVE ENVELOPE CANNOT GO
            live = envelope('sent')
            r = c.post('/lease-signing/%d/delete/' % live.pk, {'confirm': str(live.pk)})
            ok(M.LeaseSigning.objects.filter(pk=live.pk).exists(),
               'a LIVE envelope is refused, even with the number typed - '
               'cancel it first', r.status_code)
            page = c.get('/lease-signing/%d/' % live.pk).content.decode()
            ok('Delete this envelope' not in page,
               '  and its page offers no delete at all')

            # ---- A CANCELLED, UNSIGNED ONE - the case he has today
            gone = envelope('cancelled')
            files = [gone.original_pdf.name] + [
                LS.page_name(gone, n) for n in range(1, gone.page_count + 1)]
            ok(all(default_storage.exists(f) for f in files),
               'the fixture really has files to remove - %d of them' % len(files))
            page = s.get('/lease-signing/%d/' % gone.pk).content.decode()
            ok('Delete this envelope' not in page,
               'someone who is not a superuser is not offered it')
            r = s.post('/lease-signing/%d/delete/' % gone.pk, {'confirm': str(gone.pk)})
            ok(r.status_code in (302, 403)
               and M.LeaseSigning.objects.filter(pk=gone.pk).exists(),
               '  and a hand-made POST from them deletes nothing', r.status_code)
            page = c.get('/lease-signing/%d/' % gone.pk).content.decode()
            ok('Delete this envelope' in page and 'This envelope holds' not in page,
               'a superuser is offered it, with no signature warning - '
               'there are none')
            r = c.post('/lease-signing/%d/delete/' % gone.pk, {'confirm': '999999'})
            ok(M.LeaseSigning.objects.filter(pk=gone.pk).exists(),
               'a MISTYPED number deletes nothing')
            pk = gone.pk
            r = c.post('/lease-signing/%d/delete/' % pk, {'confirm': str(pk)})
            ok(r.status_code == 302 and r['Location'].rstrip('/').endswith('lease-signing')
               and not M.LeaseSigning.objects.filter(pk=pk).exists()
               and not M.LeaseSigningParty.objects.filter(signing_id=pk).exists()
               and not M.LeaseSigningEvent.objects.filter(signing_id=pk).exists(),
               'the right number deletes it - envelope, signers and history, '
               'no trace', r.get('Location'))
            ok(all(default_storage.exists(f) for f in files),
               '  and the files are STILL there until the delete commits')
            run_on_commit()
            ok(not any(default_storage.exists(f) for f in files),
               '  and gone once it has - the lease and every page image')

            # ---- A COMPLETED, SIGNED, APPROVED ONE
            done = envelope('completed', signed=2)
            done.sealed_pdf.save('sealed.pdf', ContentFile(a_pdf()), save=True)
            M.LeaseSigning.objects.filter(pk=done.pk).update(
                approved_at=timezone.now(), approved_by=boss)
            ten.tenant_lease_agreement.save('kept.pdf', ContentFile(a_pdf()), save=True)
            kept = ten.tenant_lease_agreement.name
            page = c.get('/lease-signing/%d/' % done.pk).content.decode()
            ok('This envelope holds 2 signatures.' in page
               and 'a separate copy and stays' in page,
               'a SIGNED envelope warns that 2 signatures will be destroyed, '
               'and that the tenant\'s lease stays')
            r = c.post('/lease-signing/%d/delete/' % done.pk, {'confirm': str(done.pk)})
            run_on_commit()
            ten.refresh_from_db()
            ok(not M.LeaseSigning.objects.filter(pk=done.pk).exists()
               and ten.tenant_lease_agreement.name == kept
               and default_storage.exists(kept),
               '  it can still be deleted - his decision - and the lease on '
               'the tenant record is untouched')
            raise Rollback
    except Rollback:
        pass
    finally:
        over.disable()
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'transaction.on_commit(_remove_files)'" in gate,
   '  with a sentinel on the order that makes a failed delete cost nothing')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX), '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
