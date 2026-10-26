# -*- coding: utf-8 -*-
"""test_system_round.py - round SY-1, 26 Oct 2026.

TWO SMALL SYSTEM FIXES, RELEASE 21.

    - EVERY PERMISSION EXISTS AFTER EVERY MIGRATE. The rows were only made
      when a superuser opened User Administration or the setup page, so a
      fresh or rebuilt database refused every Edit screen until somebody
      did. post_migrate now calls pages.permissions.ensure_permissions().
      The setup page and the old command looked rows up BY NAME, which
      fails on a row whose name has drifted; both go by codename now.
    - THE PUSH SWEEPS AT TWO WORKERS UNLESS TOLD OTHERWISE - his decision;
      every push was being typed with -Workers 2 or 3.
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

SUFFIX = '.bak_sysround'
ME = 'test_system_round.py'
PATCHER = 'apply_system_round.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'SY-1, 26 Oct 2026'

J = os.path.join
PERMS = J(ROOT, 'pages', 'permissions.py')
APPS = J(ROOT, 'pages', 'apps.py')
SETUP = J(ROOT, 'pages', 'views_setup.py')
CMD = J(ROOT, 'pages', 'management', 'commands',
        'create_module_permissions.py')
MW = J(ROOT, 'pages', 'middleware.py')
GATE = J(ROOT, PS1)
WK = J(ROOT, 'test_push_workers.py')
EDITED = (PERMS, APPS, SETUP, CMD, MW, GATE, WK)

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

NOW = dict((p, read(p)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def claims(src):
    pm = T.python_code_only(src[PERMS])
    ap = T.python_code_only(src[APPS])
    st = T.python_code_only(src[SETUP])
    cm = T.python_code_only(src[CMD])
    mw = T.python_code_only(src[MW])
    return [
        ('def ensure_permissions(' in pm
         and "defaults={'name': name}" in pm
         and 'for codename, name in all_codenames():' in pm,
         'ensure_permissions() makes every codename of the one list, by '
         'codename'),
        ('post_migrate.connect(_ensure_permissions, sender=self' in ap
         and "dispatch_uid='pages.ensure_permissions'" in ap,
         '  and post_migrate calls it, once per migrate'),
        ("defaults={'name': name}" in st and 'name=name,' not in st,
         'the setup page goes by codename, not by name'),
        ('permissions_data = all_codenames()' in cm
         and "defaults={'name': name}" in cm
         and "'Can access Dashboard module'" not in cm,
         '  and so does the old command, from the one list'),
        ('return ensure_permissions()' in mw
         and "'Can access Dashboard module'" not in mw,
         '  and the old middleware helper is the shared one'),
        ('[int]$Workers = 2,' in src[GATE],
         'the push sweeps at two workers unless told otherwise'),
        ("'[int]$Workers = 2,' in par" in src[WK],
         '  and test_push_workers asks for two'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
missing = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))

# ==========================================================================
head('3. DRIVEN - a missing permission comes back; a drifted name is fine')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.apps import apps as A
    from django.contrib.auth.models import Permission, User
    from django.contrib.contenttypes.models import ContentType
    from django.db import connection, transaction
    from django.db.models.signals import post_migrate
    from django.test import Client
    from pages.permissions import all_codenames
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
        Permission.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    cfg = A.get_app_config('pages')
    live = post_migrate._live_receivers(cfg)
    # Django 5 hands back (sync, async); older versions a plain list.
    live = live[0] if isinstance(live, tuple) else live
    names = [getattr(r, '__name__', '') for r in live]
    ok('_ensure_permissions' in names,
       'post_migrate really has the receiver connected for this app',
       names)
    ct = ContentType.objects.get_for_model(User)
    try:
        with transaction.atomic():
            Permission.objects.filter(
                codename__in=['can_edit_tenants', 'can_access_receipts'],
                content_type=ct).delete()
            ok(not Permission.objects.filter(
                codename='can_edit_tenants', content_type=ct).exists(),
               'CONTROL: with the row deleted, an Edit Tenant check has '
               'nothing to grant')
            # THE SIGNAL, AS migrate SENDS IT - not the function called
            # by hand, so a receiver connected to the wrong sender fails.
            post_migrate.send(sender=cfg, app_config=cfg, verbosity=0,
                              interactive=False, using='default',
                              apps=A, plan=[])
            back = set(Permission.objects.filter(
                content_type=ct,
                codename__in=['can_edit_tenants', 'can_access_receipts'])
                .values_list('codename', flat=True))
            ok(back == {'can_edit_tenants', 'can_access_receipts'},
               'one post_migrate brings both back', back)
            have = set(Permission.objects.filter(content_type=ct)
                       .values_list('codename', flat=True))
            gone = [c for c, _n in all_codenames() if c not in have]
            ok(not gone, '  and every codename of the list exists after '
               'it', gone)
            n0 = Permission.objects.count()
            post_migrate.send(sender=cfg, app_config=cfg, verbosity=0,
                              interactive=False, using='default',
                              apps=A, plan=[])
            ok(Permission.objects.count() == n0,
               '  and a second migrate creates nothing more')

            # A DRIFTED NAME - the old seeder's wording.
            Permission.objects.filter(codename='can_access_tenants',
                                      content_type=ct).update(
                name='Can access Tenants module')
            boss = User.objects.create_superuser(
                'sy1boss', 'sy1.boss@example.com', 'not-a-real-password')
            c = Client(SERVER_NAME='localhost')
            c.force_login(boss)
            r = c.get('/setup-permissions/')
            body = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200 and 'Error' not in body
               and 'completed successfully' in body,
               'the setup page completes over a row whose name drifted',
               '%s %s' % (r.status_code, body[-160:]))
            ok(Permission.objects.filter(codename='can_access_tenants',
                                         content_type=ct).count() == 1,
               '  and leaves ONE row for that codename, its name untouched')
            from django.core.management import call_command
            import io
            call_command('create_module_permissions', stdout=io.StringIO())
            ok(Permission.objects.filter(codename='can_access_tenants',
                                         content_type=ct).count() == 1,
               '  and so does the old command')
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
ok("File = 'pages/apps.py'; Text = 'post_migrate.connect(_ensure_permissions'"
   in gate, '  with a sentinel on the receiver')
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
