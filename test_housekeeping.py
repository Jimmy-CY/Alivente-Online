# -*- coding: utf-8 -*-
"""test_housekeeping.py - round HK-1, 26 Oct 2026.

RELEASE 19 HOUSEKEEPING - FOUR THINGS HE FOUND OR ASKED FOR, EACH SMALL.

    1. THE SYSTEM TAB IS FOUR CELLS AGAIN - "The tab should only be big
       enough for 4 buttons, not 6". ES-7 added a tile and kept both
       reserved blanks, so three tiles and two blanks made a third row.
    1b. THE TENANT DETAILS REPORT NAMES THE FIRST TENANT - "We don't have
       the name of the first tenant". T2-7 fixed the property page and
       missed this report.
    2. NO PAPER-PLANE ON MANAGE LEASE AGREEMENTS - "if a Lease Agreement
       is in here, it has already been signed". E-signing starts from
       Lease Signing > Start e-signing only.
    3. THE BACKGROUND JOB RUNS ONCE A DAY, AND THE HELP NOW SAYS SO - his
       Railway screenshot: 06:00 UTC daily, not every five minutes as
       nine places claimed. It cannot run more often (each run sends the
       daily digests); his decision was to keep it and fix the words.
    4. STALE PERMISSION CHECKS - migration 0065 deleted can_edit_personal,
       but 48 controls on the Recipes and Passports screens still asked
       for it, so only a superuser ever saw them. They ask can_edit_recipes
       / can_edit_passports now - what the views already enforce.
    And THE PUSH STOPS AT ONCE when the local database is missing a
    migration (Release 15 lost a 20-minute gate to exactly that).
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

SUFFIX = '.bak_housekeep'
ME = 'test_housekeeping.py'
PATCHER = 'apply_housekeeping.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'HK-1, 26 Oct 2026'

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
ADMIN_T = J(TPL, 'admin_apms.html')
TLA_T = J(TPL, 'tenant_lease_agreement.html')
REPORT_T = J(TPL, 'tenant_report.html')
HELP_A = J(ROOT, 'pages', 'help_content', 'administration.html')
HELP_O = J(ROOT, 'pages', 'help_content', 'operational.html')
TICK = J(ROOT, 'pages', 'management', 'commands', 'lease_signing_tick.py')
GATE = J(ROOT, PS1)
RECIPES = [J(TPL, n + '.html') for n in (
    'categories_management', 'ingredient_base_units_management',
    'measurement_units_management', 'recipe_management',
    'unit_conversions_management', 'view_recipe')]
PASSPORTS = J(TPL, 'passport_management.html')
EDITED = tuple([ADMIN_T, TLA_T, REPORT_T, HELP_A, HELP_O, TICK, GATE, PASSPORTS]
               + RECIPES)

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


def help_text(src):
    return src[HELP_A] + src[HELP_O]


def claims(src):
    adm = T.code_only(src[ADMIN_T])
    tla = T.code_only(src[TLA_T])
    hp = help_text(src)
    rec = [T.code_only(src[p]) for p in RECIPES]
    pas = T.code_only(src[PASSPORTS])
    gate = src[GATE]
    rep = T.code_only(src[REPORT_T])
    info = rep[rep.find('Tenant Information'):rep.find('Contact Information')]
    return [
        ('<span class="detail-label">Name:</span>' in info
         and '{{ tenant.tenant_name }}' in info,
         'the Tenant Details Report names the FIRST tenant above the '
         'contact details that are theirs'),
        # THE RESERVED CELLS LIVE ONLY IN THE SYSTEM PANEL, so the page's
        # count is the panel's.
        (adm.count('<div class="admin-btn admin-btn--reserved"') == 1,
         'the System panel is three tiles and ONE reserved cell - four, '
         'two rows'),
        ('lease_signing_create' not in tla and 'fa-paper-plane' not in tla
         and 'mobile-action-bar cols-2' in tla,
         'Manage Lease Agreements offers no paper-plane, on a desktop or '
         'a phone'),
        ('every five minutes' not in hp and 'within five minutes' not in hp
         and hp.count('once a day, each morning at about 08:00 Cyprus '
                      'time') == 3,
         'the Help says the background job runs once a day, in the '
         'morning - in all three places that describe it'),
        ('morning run, at about 08:00 Cyprus time' in src[HELP_A],
         '  and the Lease Signing help says when reminders go'),
        (all('perms.auth.can_edit_personal' not in r for r in rec)
         and all('perms.auth.can_edit_recipes' in r for r in rec)
         and 'perms.auth.can_edit_personal' not in pas
         and 'perms.auth.can_edit_passports' in pas,
         'the Recipes and Passports screens ask for the permissions that '
         'still exist'),
        ("& python manage.py migrate --check 2>&1" in gate
         and gate.find('migrate --check') < gate.find("Head 'Django system "
                                                      "check'"),
         'the push asks whether the local database is migrated, before '
         'any suite runs'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
missing = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))
left = []
for q in T.templates():
    if 'perms.auth.can_edit_personal' in T.code_only(read(q)):
        left.append(T.rel(q))
ok(not left, 'and NO template in the tree asks for can_edit_personal',
   ', '.join(left))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))

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
    from django.contrib.auth.models import Permission, User
    from django.db import connection, transaction
    from django.test import Client
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
        User.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    try:
        with transaction.atomic():
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(User)

            def grant(u, *codes):
                for code in codes:
                    u.user_permissions.add(Permission.objects.get_or_create(
                        codename=code, content_type=ct,
                        defaults={'name': code})[0])
                return User.objects.get(pk=u.pk)

            cook = grant(User.objects.create_user(
                'hk1cook', 'hk1.cook@example.com', 'not-a-real-password'),
                'can_access_recipes', 'can_edit_recipes')
            look = grant(User.objects.create_user(
                'hk1look', 'hk1.look@example.com', 'not-a-real-password'),
                'can_access_recipes')
            c = Client(SERVER_NAME='localhost')
            c.force_login(cook)
            r = c.get('/categories-management/')
            page = r.content.decode('utf-8', 'replace')
            ADD = 'data-toggle="modal" data-target="#addCategoryModal"'
            ok(r.status_code == 200 and ADD in page
               and 'title="No permission to edit"' not in page,
               'somebody who may EDIT recipes now gets a working Add Category - '
               'before this round only a superuser did', r.status_code)
            c2 = Client(SERVER_NAME='localhost')
            c2.force_login(look)
            r = c2.get('/categories-management/')
            pg2 = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200 and ADD not in pg2
               and 'title="No permission to edit"' in pg2,
               '  and somebody who may only LOOK still gets the greyed one',
               r.status_code)
            raise Rollback
    except Rollback:
        pass

# THE GATE IS ASKED, NOT READ. migrate --check is what the push runs; a
# database with every migration applied must answer 0, which is the state
# the push needs before it may run a suite.
if have_db:
    import subprocess
    pr = subprocess.run([sys.executable, 'manage.py', 'migrate', '--check'],
                        cwd=ROOT, capture_output=True, text=True,
                        timeout=300)
    ok(pr.returncode == 0,
       'migrate --check answers 0 on a migrated database, so the new gate '
       'stops nobody who is up to date',
       (pr.stdout + pr.stderr)[-400:])

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = '& python manage.py migrate --check 2>&1'" in gate,
   '  with a sentinel on the migration gate')
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
