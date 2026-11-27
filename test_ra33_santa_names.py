# -*- coding: utf-8 -*-
"""test_ra33_santa_names.py - round RA33, 27 Nov 2026.

RELEASE RA33 - SECRET SANTA EMAILS: NICKNAME (NAME), AND WHO'S TAKING PART.
Demetri, 27 Nov: "Where are the nicknames used? ... Should we list the
people that are included in the Event. For those that we have saved a
nickname, then maybe it can state the Nickname (Name)?" Agreed: the box
naming whom they drew shows the nickname over the name; the draw, test
and change emails list everyone, A to Z, names only; the reveal does the
same for their Santa. No real email leaves: locmem.
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
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra33'
ME = 'test_ra33_santa_names.py'
PATCHER = 'apply_ra33_santa_names.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
PG = J(ROOT, 'pages')
T = J(PG, 'templates')

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
    if not os.path.isfile(p):
        return ''
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

head('1. THE SOURCE')
santa = read(J(PG, 'santa.py'))
helpt = read(J(PG, 'help_content', 'administration.html'))
ok('def shown(' in santa and 'def roster(' in santa, 'NAMES: nickname over name, and the roster')
ok("Who&rsquo;s taking part" in santa and '.email' not in santa.split('def roster(')[1].split('def ')[0],
   'THE LIST carries names only - no email addresses')
ok('Nickname (Name)' in helpt, 'HELP says so')

head('2. DRIVEN')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']
_dj.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass


try:
    from django.core import mail
    from django.db import transaction
    from django.contrib.auth.models import User
    from django.utils import timezone
    from pages.models import SantaExchange, SantaPair, SantaPerson
    from pages import santa as SS

    with transaction.atomic():
        me = User.objects.create_user('ss33', 'p33@example.com', 'x', first_name='Demetri')
        ex = SantaExchange.objects.create(owner=me, year=2026, title='Full Manias Family', budget=40)
        P = {}
        for f, s, n, e in (('Demetri', 'Manias', 'Papa', 'd33@example.com'),
                           ('Angie', 'Manias', '', 'a33@example.com'),
                           ('Alexandra', 'Manias', 'Alex', 'x33@example.com'),
                           ('Erene', 'Manias', 'erene manias', 'e33@example.com')):
            P[f] = SantaPerson.objects.create(exchange=ex, first_name=f, surname=s, nickname=n, email=e)
        ok(SS.label(P['Demetri']) == 'Papa (Demetri Manias)' and SS.label(P['Angie']) == 'Angie Manias',
           'LABEL: Papa (Demetri Manias); no nickname, just the name')
        ok(SS.label(P['Erene']) == 'Erene Manias', '  a nickname that only repeats the name is not doubled')
        ok(SS.roster(ex) == ['Alex (Alexandra Manias)', 'Angie Manias', 'Erene Manias', 'Papa (Demetri Manias)'],
           'THE ROSTER: everyone, A to Z')
        ring = [('Demetri', 'Angie'), ('Angie', 'Alexandra'), ('Alexandra', 'Erene'), ('Erene', 'Demetri')]
        for g, r in ring:
            SantaPair.objects.create(exchange=ex, giver=P[g], receiver=P[r])
        ex.drawn_at = timezone.now()
        ex.save()
        mail.outbox = []
        SS.send_kind(ex, 'draw')
        by = {m.to[0]: m for m in mail.outbox}
        m = by['e33@example.com']                     # Erene drew Demetri
        h = m.alternatives[0][0]
        ok('>Papa</div>' in h and '>Demetri Manias</div>' in h, 'THE BOX: Papa large, Demetri Manias under it')
        ok('Papa' in m.body and '(Demetri Manias)' in m.body, '  and in the plain-text email')
        ok("Who&rsquo;s taking part (4)" in h and '<li>Alex (Alexandra Manias)</li>' in h
           and '<li>Angie Manias</li>' in h, 'WHO\'S TAKING PART: listed in the draw email')
        ok(all('33@example.com' not in mm.alternatives[0][0] and '33@example.com' not in mm.body for mm in mail.outbox),
           '  names only - nobody\'s address is in anyone\'s email')
        ok(len({mm.alternatives[0][0].split("taking part")[1].split('</ul>')[0] for mm in mail.outbox}) == 1,
           '  the same list for everyone, so it gives nothing away')
        h2 = by['a33@example.com'].alternatives[0][0]                 # Angie drew Alexandra
        ok('>Alex</div>' in h2 and '>Alexandra Manias</div>' in h2, '  Alex (Alexandra Manias) for whoever drew her')
        h3 = by['d33@example.com'].alternatives[0][0]                 # Demetri drew Angie
        ok('>Angie Manias</div>' in h3 and 'Angie Manias</div><div' not in h3.split('your secret recipient')[1][:200],
           '  no nickname: the name alone, no second line')
        mail.outbox = []
        SS.send_kind(ex, 'week')
        ok(len(mail.outbox) == 4 and 'taking part' not in mail.outbox[0].alternatives[0][0],
           'THE REMINDERS stay short: no list')
        mail.outbox = []
        SS.send_kind(ex, 'reveal')
        h4 = {mm.to[0]: mm for mm in mail.outbox}['a33@example.com'].alternatives[0][0]  # Angie's Santa: Demetri
        ok('>Papa</div>' in h4 and '>Demetri Manias</div>' in h4, 'THE REVEAL: your Santa as Papa (Demetri Manias)')
        mail.outbox = []
        SS.send_kind(ex, 'change', only={P['Erene'].pk})
        ok(len(mail.outbox) == 1 and 'taking part (4)' in mail.outbox[0].alternatives[0][0],
           'CHANGE OF PLAN carries the list too')
        _s, _t, hp = SS.message(ex, 'test', SantaPerson(first_name='Demetri'), "Your recipient's name")
        ok("Your recipient&#x27;s name" in hp and 'taking part (4)' in hp, 'THE TEST / PREVIEW shows the list as it will go')
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 2 ran', str(e)[:200])

head('3. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
