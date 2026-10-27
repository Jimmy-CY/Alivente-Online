# -*- coding: utf-8 -*-
"""test_lease_status.py - round LS-1, 27 Oct 2026.

RELEASE 26 - LEASE SIGNING STATUS, AND THREE BACKLOG FIXES.

    - LEASE SIGNING STATUS, his decision: Stella can see Tenants and Lease
      Signing is superuser only, so Tenants gets a READ-ONLY report of
      where every lease out for signature stands - four boxes, one row per
      envelope in plain words, who still has to sign, when the link lapses.
      No envelope links, no documents, nothing that acts. Approved render
      of 27 October.
    - fsr_commit OPENS THE ISSUE IT SAVED, not the newest in the table (two
      people adding at once were sent to each other's), and a form that
      does not validate says so instead of landing on somebody else's.
    - THE DAILY JOB'S lease-upload reminder and passport/ID expiry email go
      through _send_email_with_retry like the main notification, and the
      duplicate recipients lookup is gone.
    - (Re-measured and already gone: the doubled @permission_required.)
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

SUFFIX = '.bak_leasestatus'
ME = 'test_lease_status.py'
PATCHER = 'apply_lease_status.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'LS-1, 27 Oct 2026'

J = os.path.join
VIEW = J(ROOT, 'pages', 'views', 'lease_signing_status.py')
PAGE = J(ROOT, 'pages', 'templates', 'tenant_lease_signing_status.html')
URLS = J(ROOT, 'pages', 'urls.py')
VINIT = J(ROOT, 'pages', 'views', '__init__.py')
TEN_T = J(ROOT, 'pages', 'templates', 'tenant.html')
HELP_O = J(ROOT, 'pages', 'help_content', 'operational.html')
ISSUES = J(ROOT, 'pages', 'views', 'issues.py')
CHECK = J(ROOT, 'pages', 'management', 'commands',
          'check_lease_renewal_and_invoices.py')
GATE = J(ROOT, PS1)
EDITED = (URLS, VINIT, TEN_T, HELP_O, ISSUES, CHECK)
SHIPPED = (VIEW, PAGE)

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


def between(s, a, b):
    i = s.find(a)
    j = s.find(b, i + 1) if i >= 0 else -1
    return s[i:j] if i >= 0 and j > i else ''


def claims(src):
    v = T.python_code_only(src.get(VIEW, ''))
    pg = T.code_only_js(src.get(PAGE, ''))
    iss = T.python_code_only(src[ISSUES])
    fc = between(iss, 'def fsr_commit(request)', '\ndef ')
    ck = T.python_code_only(src[CHECK])
    up = between(ck, 'def send_new_lease_upload_reminder(', '\n    def ')
    pp = between(ck, 'def _send_passport_expiry_email_for_workspace(',
                 '\n    def ')
    return [
        ("@permission_required('auth.can_access_tenants'" in v
         and 'superuser_only' not in v and 'def lease_signing_status(' in v,
         'Lease Signing Status is a Tenants report - behind the Tenants '
         'permission, not the superuser gate'),
        (bool(pg) and 'lease_signing_detail' not in pg
         and 'lease_signing_sealed' not in pg and '<form' not in pg
         and 'original_pdf' not in pg,
         '  and read only - no envelope link, no document, no form'),
        ("name='lease_signing_status'" in src[URLS]
         and 'from .lease_signing_status import *' in src[VINIT],
         '  routed and exported'),
        (src[TEN_T].count("{% url 'lease_signing_status' %}") == 2,
         '  and offered on Tenants, in the reports menu and on the phone'),
        ('<strong>Lease Signing Status</strong>' in src[HELP_O],
         '  and the Tenants help describes it'),
        ('saved = form.save()' in fc and 'args=[saved.pk]' in fc
         and "order_by('-issues_id')" not in fc
         and 'The issue was not saved' in fc,
         'fsr_commit opens the issue it saved, and says so when it saved '
         'nothing'),
        ('self._send_email_with_retry(' in up
         and 'self._send_email_with_retry(' in pp
         and '.sendmail(' not in up and '.sendmail(' not in pp
         and up.count("get_email_recipients('new_lease_upload')") == 1,
         'the lease-upload reminder and the passport/ID expiry email go '
         'through the retrying sender, recipients read once'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
missing = [os.path.relpath(p, ROOT) for p in EDITED + SHIPPED
           if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
before = dict(OLD)
before[VIEW] = ''
before[PAGE] = ''
held = [m for c, m in claims(before) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))
for p in SHIPPED:
    ok(not os.path.isfile(p + SUFFIX),
       'CONTROL: %s has no backup, because this round INVENTED it'
       % os.path.basename(p))

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    import datetime as dt
    from django.contrib.auth.models import Permission, User
    from django.db import connection, transaction
    from django.db.models.signals import post_save
    from django.test import Client
    from django.utils import timezone
    import pages.models as M
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

if have_db:
    try:
        with transaction.atomic():
            from pages.permissions import ensure_permissions
            ensure_permissions()
            now = timezone.now()
            n = [0]

            def a_ten(name, **kw):
                n[0] += 1
                p = M.props.objects.create(prop_name='LS1 Flat %d' % n[0],
                                           prop_country='Cyprus')
                return M.tenant.objects.create(
                    prop=p, tenant_type='Individual', tenant_name=name,
                    tenant_lease_start_date=dt.date(2027, 1, 1),
                    tenant_lease_end_date=dt.date(2027, 12, 31),
                    tenant_current='No', **kw)

            def an_env(ten, status, parties, **kw):
                e = M.LeaseSigning.objects.create(
                    tenant=ten, source='uploaded', status=status,
                    expires_at=now + dt.timedelta(days=5), **kw)
                for i, (nm, role, signed, declined) in enumerate(parties):
                    M.LeaseSigningParty.objects.create(
                        signing=e, role=role, order=i, name=nm,
                        email='ls1-%d-%d@example.com' % (e.pk, i),
                        signed_at=now if signed else None,
                        declined_at=now if declined else None)
                return e

            H = ('House Signer', 'alivente', True, False)
            draft = an_env(a_ten('LS1 Draft Tenant'), 'draft',
                           [('House Signer', 'alivente', False, False),
                            ('LS1 Draft Tenant', 'tenant', False, False)])
            sent = an_env(a_ten('LS1 Solo Tenant'), 'sent', [
                H, ('LS1 Solo Tenant', 'tenant', False, False)],
                sent_at=now)
            part = an_env(a_ten('LS1 First', tenant_2_name='LS1 Second'),
                          'part_signed', [
                              H, ('LS1 First', 'tenant', True, False),
                              ('LS1 Second', 'tenant', False, False)],
                          sent_at=now)
            waiting = an_env(a_ten('LS1 Waiting Approval'), 'completed', [
                H, ('LS1 Waiting Approval', 'tenant', True, False)],
                sent_at=now, completed_at=now)
            M.LeaseSigning.objects.filter(pk=waiting.pk).update(
                sealed_pdf='lease_signing/sealed/ls1.pdf')
            declined = an_env(a_ten('LS1 Decliner'), 'declined', [
                H, ('LS1 Decliner', 'tenant', False, True)], sent_at=now)
            filed = an_env(a_ten('LS1 Filed Tenant'), 'completed', [
                H, ('LS1 Filed Tenant', 'tenant', True, False)],
                sent_at=now, completed_at=now, approved_at=now)

            staff = User.objects.create_user(username='ls1stella',
                                             password='not-a-real-password')
            staff.user_permissions.add(
                Permission.objects.get(codename='can_access_tenants'))
            staff = User.objects.get(pk=staff.pk)
            c = Client(SERVER_NAME='localhost')
            c.force_login(staff)
            r = c.get('/tenant-lease-signing/')
            body = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200,
               'a non-superuser who can see Tenants opens the report',
               r.status_code)
            ok(c.get('/lease-signing/').status_code in (302, 403),
               '  while Lease Signing itself stays closed to them')
            for words, who in (
                    ('Waiting for Alivente to sign first', 'the draft'),
                    ('With the tenant to sign', 'one tenant, unsigned'),
                    ('With the tenants - 1 of 2 signed', 'joint, half'),
                    ('Signed by everyone - awaiting Alivente approval',
                     'signed, not yet approved'),
                    ('Declined by LS1 Decliner', 'the refusal')):
                ok(words in body, '  says "%s" for %s' % (words, who))
            ok('LS1 Second' in body.split('LS1 First', 1)[-1][:2000],
               '  names who still has to sign')
            ok('LS1 Filed Tenant' not in body,
               '  and leaves out a lease already signed and filed')
            ok(not re.search(r'/lease-signing/\d+', body),
               '  with no link to any envelope')
            body = c.get('/tenant-lease-signing/?all=1').content.decode(
                'utf-8', 'replace')
            ok('LS1 Filed Tenant' in body
               and 'Complete - signed lease filed on the tenancy' in body,
               'Include finished shows it, as complete')

            nobody = User.objects.create_user(username='ls1nobody',
                                              password='not-a-real-password')
            c2 = Client(SERVER_NAME='localhost')
            c2.force_login(nobody)
            ok(c2.get('/tenant-lease-signing/').status_code == 403,
               'and a user without Tenants is refused')

            # ---- fsr_commit
            editor = User.objects.create_user(
                username='ls1editor', password='not-a-real-password')
            for code in ('can_access_issues', 'can_edit_issues'):
                editor.user_permissions.add(
                    Permission.objects.get(codename=code))
            editor = User.objects.get(pk=editor.pk)
            ce = Client(SERVER_NAME='localhost')
            ce.force_login(editor)
            prop = M.props.objects.create(prop_name='LS1 Issue Flat',
                                          prop_country='Cyprus')

            # A SECOND PERSON ADDS AN ISSUE THE MOMENT THIS ONE SAVES -
            # the race, made to happen every time.
            made = []

            def racer(sender, instance, created, **kw):
                # THE FLAG FIRST - the row this makes fires the signal too.
                if created and not made:
                    made.append(None)
                    made[0] = M.issues.objects.create(
                        prop=prop, issues_heading='LS1 someone else')
            post_save.connect(racer, sender=M.issues,
                              dispatch_uid='ls1-racer')
            try:
                r = ce.post('/fsr_commit/', {
                    'prop': prop.pk, 'issues_heading': 'LS1 mine',
                    'issues_status': 'Open',
                    'issues_date_logged': '2026-10-27'})
            finally:
                post_save.disconnect(sender=M.issues,
                                     dispatch_uid='ls1-racer')
            mine = M.issues.objects.filter(issues_heading='LS1 mine').first()
            ok(mine is not None and made
               and made[0].pk > mine.pk
               and r.status_code == 302
               and '/%d' % mine.pk in r['Location'],
               'fsr_commit opens the issue it saved, even when somebody '
               'else\'s landed after it',
               r.get('Location'))
            n0 = M.issues.objects.count()
            r = ce.post('/fsr_commit/', {'issues_heading': 'LS1 no prop'})
            ok(r.status_code == 302 and r['Location'].endswith('/fsr_add/')
               and M.issues.objects.count() == n0,
               '  and a form that does not validate saves nothing and goes '
               'back to the form', r.get('Location'))
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = \"@permission_required('auth.can_access_tenants'\"" in gate,
   '  with a sentinel that would notice the report losing its permission')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.relpath(p, ROOT))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
