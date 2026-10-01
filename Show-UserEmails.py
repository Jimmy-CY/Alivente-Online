# -*- coding: utf-8 -*-
"""Show-UserEmails.py - who could still get into this system once email
   is the only way to set a password.

    python Show-UserEmails.py            every user
    python Show-UserEmails.py --risk     only the accounts that are a problem

Run from the repo root. READ-ONLY - it opens a database connection, reads,
and writes nothing. No user, profile or password is touched by this tool.

WHY IT EXISTS, AND WHY IT IS THE FIRST THING BUILT

  Agreed with Demetri, 1 Oct 2026: the administrator stops typing
  passwords. A new user is created with no usable password and an email
  invites them to choose one; a reset sends the same kind of email. The
  password field comes off user_add and user_edit.

  THAT CLOSES A DOOR. Today you can always set somebody's password by
  hand. Afterwards, an account's only route in through the UI is an email
  to the address on its record - so an account with NO EMAIL ADDRESS has
  no route in at all.

  The dangerous case is a SUPERUSER with no email. Every reset in the new
  flow is triggered by a superuser, and Forgot Password mails the address
  on the account. A superuser with no address can neither be reset by
  anyone nor reset themselves. That is a locked door with the key inside.

  So this is asked of YOUR DATA before the change is built, not after.
  The same habit as Show-ProjectRollup.py, which was written first
  precisely so a question about live rows was answered from live rows.

WHAT IT REPORTS

  Per user: username, email (or the absence of one), whether the account
  is active, whether it is a superuser or staff, whether it has a usable
  password at all, and when it last logged in.

  Then three counts that decide whether the round needs anything extra:

    * accounts with no email                 - cannot be reset at all
    * SUPERUSERS with no email               - the locked-door case
    * duplicate email addresses              - two accounts, one inbox.
                                               Forgot Password matches on
                                               the address, so a duplicate
                                               makes "which account did I
                                               just reset" ambiguous.

  It also names the accounts with an UNUSABLE password already, because
  those are the ones that are currently unreachable and would be fixed,
  not broken, by the new flow.

WHAT IT DOES NOT DO

  It reads no password and prints no password. Django stores a hash, and
  the only thing asked of it here is has_usable_password(), which is a
  boolean about the shape of the hash and reveals nothing about the
  secret.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the database, and a username or a
# first name may not be ASCII. On Windows, Python writes stdout as cp1252
# whenever it is not a UTF-8 console, and cp1252 cannot encode Greek: the
# print itself raises UnicodeEncodeError and the run dies part-way
# through. A crash says far less about why than a failure does.
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
import sys

ARGS = sys.argv[1:]
ONLY_RISK = '--risk' in ARGS

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django                                                    # noqa: E402
django.setup()                                                   # noqa: E402

from collections import Counter                                  # noqa: E402
from django.contrib.auth.models import User                      # noqa: E402

# A TOOL THAT CAN RUN AGAINST TWO DATABASES MUST SAY WHICH ONE IT IS ON.
# The same line the rollup tools print, for the same reason: a production
# question was once answered from the development database twice. See
# pages/db_banner.py.
from pages.db_banner import print_banner                         # noqa: E402

BAR = '=' * 78


def role_of(u):
    if u.is_superuser:
        return 'SUPERUSER'
    if u.is_staff:
        return 'staff'
    return 'user'


print(BAR)
print('Show-UserEmails.py - who can still get in once email is the only way')
print(BAR)
print_banner()
print('')
print('READ-ONLY. Nothing is written. No password is read or printed.')
print('')

users = list(User.objects.all().order_by('-is_superuser', 'username'))
if not users:
    print('No users at all. That is itself worth knowing.')
    raise SystemExit(0)

# ---- the per-user table -------------------------------------------------
no_email = [u for u in users if not (u.email or '').strip()]
su_no_email = [u for u in no_email if u.is_superuser]
counts = Counter((u.email or '').strip().lower()
                 for u in users if (u.email or '').strip())
dupes = {e: n for e, n in counts.items() if n > 1}
unusable = [u for u in users if not u.has_usable_password()]

risky = set(u.pk for u in no_email) | set(u.pk for u in unusable)
for u in users:
    if (u.email or '').strip().lower() in dupes:
        risky.add(u.pk)

shown = [u for u in users if (u.pk in risky)] if ONLY_RISK else users
if ONLY_RISK and not shown:
    print('Nothing at risk. Every account has an email, every address is')
    print('unique, and every account has a usable password.')
else:
    print('%-22s %-34s %-10s %-7s %-8s %s'
          % ('USERNAME', 'EMAIL', 'ROLE', 'ACTIVE', 'PASSWORD', 'LAST LOGIN'))
    print('-' * 78)
    for u in shown:
        email = (u.email or '').strip()
        flag = ''
        if not email:
            flag = '  <-- NO EMAIL'
            if u.is_superuser:
                flag = '  <-- NO EMAIL, AND A SUPERUSER'
        elif email.lower() in dupes:
            flag = '  <-- shared address'
        print('%-22s %-34s %-10s %-7s %-8s %s%s'
              % (u.username[:22],
                 (email or '(none)')[:34],
                 role_of(u),
                 'yes' if u.is_active else 'NO',
                 'usable' if u.has_usable_password() else 'UNUSABLE',
                 u.last_login.strftime('%Y-%m-%d') if u.last_login
                 else 'never',
                 flag))

# ---- the three counts that decide the round ----------------------------
print('')
print(BAR)
print('WHAT THIS MEANS FOR THE ROUND')
print(BAR)
print('  %d user(s) in total, %d active'
      % (len(users), sum(1 for u in users if u.is_active)))
print('')

print('  %d account(s) with NO EMAIL - these cannot be reset at all once'
      % len(no_email))
print('      the admin password field is gone.')
for u in no_email:
    print('        %s  (%s, %s)'
          % (u.username, role_of(u), 'active' if u.is_active else 'disabled'))

print('')
if su_no_email:
    print('  *** %d SUPERUSER(S) WITH NO EMAIL. This is the locked-door case.'
          % len(su_no_email))
    for u in su_no_email:
        print('        %s' % u.username)
    print('      Give each of these an address BEFORE the round ships, or')
    print('      the account has no route in through the UI at all. The')
    print('      break-glass path would be manage.py changepassword on')
    print('      Railway, which does not need mail - but that is a last')
    print('      resort, not a plan.')
else:
    print('  No superuser is missing an email. The locked-door case does not')
    print('  exist in this database.')

print('')
if dupes:
    print('  %d email address(es) used by more than one account:' % len(dupes))
    for e, n in sorted(dupes.items()):
        who = [u.username for u in users
               if (u.email or '').strip().lower() == e]
        print('        %-34s %d accounts: %s' % (e, n, ', '.join(who)))
    print('      Forgot Password matches on the address, so a shared inbox')
    print('      makes "which account did I just reset" ambiguous. Worth')
    print('      deciding before the round: refuse duplicates, or send one')
    print('      link per matching account and name the username in each.')
else:
    print('  Every email address belongs to exactly one account.')

print('')
if unusable:
    print('  %d account(s) already have an UNUSABLE password:' % len(unusable))
    for u in unusable:
        print('        %-22s %s'
              % (u.username, (u.email or '(no email)')))
    print('      These cannot log in today. The new flow FIXES them, as long')
    print('      as they have an address to send to.')
else:
    print('  Every account has a usable password today.')

print('')
print(BAR)
print('  Nothing was written. Run it again after any change and compare.')
print(BAR)
