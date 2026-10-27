# -*- coding: utf-8 -*-
"""test_strip_gone.py - round ES-11, 26 Oct 2026.

THE YELLOW SIGNED-LEASES BAR IS GONE - his decision of 26 October, from
the Notifications screen on Live: "Do we need the top yellow bar, if we
have the box below?" - and on Home too.

ES-6 put a yellow "N signed leases waiting for your approval" bar at the
top of Home and Notifications on 25 October. Release 23 then gave each page
its own place for the same count: Home's Waiting for you card has a row for
signed leases, and Notifications has the Leases Needing Action box. Two
places saying one thing on one screen is noise, so the bar goes from both.

The count itself stays: the context processor still supplies
lease_approvals_waiting to the bell, the Home row and the box.

AND THE TENANT TOGGLE SAYS "NON-ACTIVE" - his second decision the same
evening, from Manage Lease Agreements: "Include past tenants" also shows
FUTURE tenancies, so the button now reads "Include non-active tenants",
and its partner "Active tenants only", on Tenants, Manage Lease
Agreements and Payment Days alike. The help follows.
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

SUFFIX = '.bak_stripgone'
ME = 'test_strip_gone.py'
PATCHER = 'apply_strip_gone.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-11, 26 Oct 2026'

J = os.path.join
HOME_T = J(ROOT, 'pages', 'templates', 'home.html')
ND_T = J(ROOT, 'pages', 'templates', 'notifications.html')
TLA = J(ROOT, 'test_lease_approval.py')
CTX = J(ROOT, 'mysite', 'context_processors.py')
TEN_T = J(ROOT, 'pages', 'templates', 'tenant.html')
TLA_T = J(ROOT, 'pages', 'templates', 'tenant_lease_agreement.html')
TPD_T = J(ROOT, 'pages', 'templates', 'tenant_payment_days.html')
HELP_O = J(ROOT, 'pages', 'help_content', 'operational.html')
GATE = J(ROOT, PS1)
TOGGLES = (TEN_T, TLA_T, TPD_T)
EDITED = (HOME_T, ND_T, TLA) + TOGGLES + (HELP_O,)

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
    hm = T.code_only_js(src[HOME_T])
    nd = T.code_only_js(src[ND_T])
    return [
        ('lsa-strip' not in hm and 'waiting for your approval' not in hm
         and 'Signed lease{{ lease_approvals_waiting|pluralize }} awaiting '
             'approval' in hm,
         'Home has no yellow bar - the Waiting for you row carries the count'),
        ('lsa-strip' not in nd and 'waiting for your approval' not in nd
         and 'data-category="lease_action"' in nd,
         'Notifications has no yellow bar - the Leases Needing Action box '
         'carries it'),
        ("'lsa-strip' in mk[HOME]" not in src[TLA]
         and 'data-category="lease_action"\' in mk[NOTIF]' in src[TLA],
         'test_lease_approval asks for the row and the box, not the bar'),
        (all('Include non-active tenants' in src[p]
             and 'Active tenants only' in src[p]
             and 'Include past tenants' not in src[p]
             and 'Current tenants only' not in src[p] for p in TOGGLES),
         'the tenant toggle says "Include non-active tenants" / "Active '
         'tenants only" on all three pages'),
        ('<em>Include non-active tenants</em>' in src[HELP_O]
         and '<em>Include past tenants</em>' not in src[HELP_O],
         '  and the help uses the same words'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
ok("'lease_approvals_waiting'" in read(CTX),
   '  and the count is still supplied, to the bell and both pages')
missing = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))
ok('class="lsa-strip"' in OLD[HOME_T] and 'class="lsa-strip"' in OLD[ND_T],
   'CONTROL: and both pages really did draw the bar before it')

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
    from django.contrib.auth.models import User
    from django.db import connection
    from django.test import Client
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('section 3', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

have_db = False
if django_up:
    try:
        connection.ensure_connection()
        User.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    # NOT IN A TRANSACTION. Home builds the notification data, and that
    # code closes Django's connection (the legacy mysql.connector block);
    # inside atomic() that would break the rollback. The one row this
    # writes is deleted in the finally instead.
    user = User.objects.create_user(
        username='es11viewer', password='not-a-real-password',
        email='viewer@example.com')
    try:
        user.is_superuser = True
        user.save()
        c = Client(SERVER_NAME='localhost')
        c.force_login(user)
        r = c.get('/notifications/')
        body = r.content.decode('utf-8', 'replace')
        ok(r.status_code == 200, 'Notifications opens', r.status_code)
        ok('lsa-strip' not in body
           and 'waiting for your approval' not in body,
           '  with no yellow bar')
        ok('data-category="lease_action"' in body,
           '  and the Leases Needing Action box still there')
        r = c.get('/')
        body = r.content.decode('utf-8', 'replace')
        ok(r.status_code == 200, 'Home opens', r.status_code)
        ok('lsa-strip' not in body
           and 'waiting for your approval' not in body,
           '  with no yellow bar')
        for url in ('/tenant/', '/tenant_lease_agreement/'):
            r = c.get(url)
            body = r.content.decode('utf-8', 'replace')
            # THE ANCHOR, not the page: base.html's CSS notes still say
            # "Include past tenants" in a comment the page carries.
            ok(r.status_code == 200
               and '</i> Include non-active tenants' in body
               and '</i> Include past tenants' not in body,
               '%s offers "Include non-active tenants"' % url,
               r.status_code)
            r = c.get(url + '?all=1')
            body = r.content.decode('utf-8', 'replace')
            ok('</i> Active tenants only' in body
               and '</i> Current tenants only' not in body,
               '  and, widened, "Active tenants only"')
    finally:
        User.objects.filter(pk=user.pk).delete()

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("File = 'pages/templates/home.html'; Text = 'lsa-strip'; Absent = $true"
   in gate, '  with a sentinel that would notice the bar coming back')
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
