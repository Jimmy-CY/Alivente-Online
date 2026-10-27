# -*- coding: utf-8 -*-
"""test_housekeeping_two.py - round HK-2, 27 Oct 2026.

RELEASE 27 - HOUSEKEEPING, from the September backlog, each item
re-measured against the tree before it was touched.

    - railway.json LOSES ITS DEAD "crons" ENTRY. It named a command that
      does not exist (check_lease_renewals) every five minutes, and Railway
      never ran it: the real schedule is cron-service's own start command,
      which runs check_lease_renewal_and_invoices at 06:00 UTC (confirmed
      in his Railway settings, 27 Oct). The build section is unchanged.
    - THE PASSPORT AND RECIPE HELP sections asked for can_access_personal,
      which migration 0065 deleted - so nobody but a superuser could see
      them. They now ask for can_access_passports and can_access_recipes.
    - THE SECOND projects/<id>/assignees/ ROUTE goes: Django only ever
      matched the first, and nothing reverses the second name.

Re-measured and already done, so not touched: the finance commit views
(every one reports a failed save), the doubled @permission_required, and
the title-deeds docstring (the view it names exists).
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

import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_housekeep2'
ME = 'test_housekeeping_two.py'
PATCHER = 'apply_housekeeping_two.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'HK-2, 27 Oct 2026'

J = os.path.join
RAIL = J(ROOT, 'railway.json')
HELP_A = J(ROOT, 'pages', 'help_content', 'administration.html')
URLS = J(ROOT, 'pages', 'urls.py')
GATE = J(ROOT, PS1)
EDITED = (RAIL, HELP_A, URLS)
MARKED = (HELP_A, URLS)      # JSON has no comments, so railway.json cannot

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


def section(src, slug):
    i = src.find('data-module-slug="%s"' % slug)
    return src[i:i + 400] if i >= 0 else ''


def claims(src):
    try:
        rj = json.loads(src[RAIL])
    except ValueError:
        rj = {}
    return [
        ('crons' not in rj and 'check_lease_renewals' not in src[RAIL]
         and rj.get('build', {}).get('installCommand'),
         'railway.json has no dead cron entry, and keeps its build section'),
        ('data-module-permission="can_access_passports"'
         in section(src[HELP_A], 'passport_management')
         and 'data-module-permission="can_access_recipes"'
         in section(src[HELP_A], 'recipe_management')
         and 'data-module-permission="can_access_personal"' not in src[HELP_A],
         'the Passport and Recipe help ask for permissions that exist'),
        (src[URLS].count("projects/<int:project_id>/assignees/'") == 1
         and "name='get_project_assignees'" not in src[URLS],
         'projects/<id>/assignees/ is routed once'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
missing = [os.path.relpath(p, ROOT) for p in MARKED if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file that can carry it',
   ', '.join(missing))

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
    from django.urls import resolve, reverse
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('section 3', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


class Rollback(Exception):
    """Nothing this suite writes survives it."""


if django_up:
    ok(resolve(reverse('project_assignees', args=[1])).url_name
       == 'project_assignees',
       'project_assignees still resolves to its view')
    have_db = False
    try:
        connection.ensure_connection()
        User.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('the help visibility', 'no database: %s'
             % str(_e).split('\n')[0][:70])
    if have_db:
        try:
            with transaction.atomic():
                from pages.permissions import ensure_permissions
                from pages.views import help as H
                ensure_permissions()
                grouped = H.get_all_modules_grouped()
                mods = {}
                for g in grouped:
                    for m in g['direct_modules']:
                        mods[m.get('slug')] = m
                    for s in g['subsections']:
                        for m in s['modules']:
                            mods[m.get('slug')] = m
                u = User.objects.create_user(username='hk2viewer',
                                             password='not-a-real-password')
                for code in ('can_access_passports', 'can_access_recipes'):
                    u.user_permissions.add(
                        Permission.objects.get(codename=code))
                u = User.objects.get(pk=u.pk)
                nobody = User.objects.create_user(
                    username='hk2nobody', password='not-a-real-password')
                for slug in ('passport_management', 'recipe_management'):
                    m = mods.get(slug)
                    ok(m is not None and H._user_can_see_module(u, m),
                       'a user with the module\'s permission sees the %s '
                       'help' % slug)
                    ok(m is not None
                       and not H._user_can_see_module(nobody, m),
                       '  and a user without it does not')
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
ok("Text = 'data-module-permission=\"can_access_personal\"'; Absent = $true"
   in gate, '  with a sentinel that would notice the deleted permission '
   'coming back')
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
