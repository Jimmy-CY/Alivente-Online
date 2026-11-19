# -*- coding: utf-8 -*-
"""test_ra01_trip_cards.py - round RA01, 18 Nov 2026.

RELEASE RA01 - TRAVEL: COMPARE IN THE CARD, PROPER DROP-DOWNS.
Demetri, 18 Nov, after R100: "How better can better do the Compare
tickboxes? Make it look better. Can it be in the trip box? I don't like
how the Country dropdown looks. The year dropdown doesn't have any
values? It had the two years just a little while back." (The years were
there; pressing the chip beside the browser's own list only focused it.)
Now each card has Compare in its own footer, a ticked card is outlined
and the button counts them; Year and Country open our own drop-down
from anywhere on the chip, each choice with its count.
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

SUFFIX = '.bak_ra01'
ME = 'test_ra01_trip_cards.py'
PATCHER = 'apply_ra01_trip_cards.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')

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
        raise IOError('%s is not on disk, so the control section cannot run.'
                      % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)






print(__doc__.strip().splitlines()[0])
import datetime as dt                                       # noqa: E402
TA = J(ROOT, 'travel')
TT = J(TA, 'templates', 'travel')

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
inc = read(J(TT, '_trip_filters.html'))
ok('<select' not in inc and inc.count('<details class="tv-dd"') == 2,
   "THE MENUS: our own drop-downs, not the browser's list")
ok('{% for o in F.year_menu %}<a href="{{ o.url }}">' in inc and
   '{% for o in F.country_menu %}<a href="{{ o.url }}">' in inc,
   '  every choice a link that keeps the other picks')
ok("details.tv-dd[open]" in inc and "'Escape'" in inc,
   '  one open at a time; Escape or a press elsewhere closes it')
st = read(J(TT, '_style.html'))
ok('.tv-pop {' in st and '.tv-dd > summary::-webkit-details-marker' in st,
   '  styled on the computer')
ok('.tv-pop {' in read(J(TA, 'assets', 'travel.css')),
   '  and on the phone')
tr = read(J(TT, 'trips.html'))
card = tr[tr.index('<div class="tv-pickcard form-card">'):
          tr.index('{% empty %}')]
ok('data-compare-pick' in card and card.index('data-compare-pick') <
   card.rindex('</div>'),
   'COMPARE IN THE CARD: the tick sits in the card\'s own footer')
ok('.tv-pickcard:has(input:checked) {' in st and 'data-compare-n' in tr,
   '  a ticked card is outlined, and the button counts them')
ok('.tv-pickcard .tv-pick input { position: absolute; opacity: 0;' in st and
   '\n.tv-pick input { width: 18px; height: 18px; }' in st,
   '  the hidden box is only inside a card - the Compare page keeps its '
   'own visible boxes')
ph = read(J(TA, 'phone.py'))
# RA03, 19 Nov 2026 - tv17-1 or later (it moves with every new look).
_v = re.search(r"SW_VERSION = 'tv(\d+)-(\d+)'", ph)
ok(_v and int(_v.group(1)) >= 17 and
   read(J(TT, 'm', 'base.html')).count('?v=tv%s-%s' % _v.groups()) == 2,
   'THE PHONE APP fetches the new look (tv17-1 or later)')
try:
    ok('<select name="year"' in was(J(TT, '_trip_filters.html')),
       "CONTROL: before this round the menus were the browser's list")
except IOError as _e:
    skip('control', str(_e))

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from pages.models import UserProfile
    from travel.models import Trip
    connection.ensure_connection()
    Trip.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

PHONE = ('Mozilla/5.0 (Linux; Android 15; SM-S936B) AppleWebKit/537.36 '
         'Chrome/131.0 Mobile Safari/537.36')

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perm, _ = Permission.objects.get_or_create(
                codename='can_access_travel', content_type__app_label='auth',
                defaults={'name': 'can_access_travel'})
            u = User.objects.create_user('ra01a', 'ra01a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            today = timezone.localdate()
            for name, back, c in (('RA01 Athens', 20, 'Greece'),
                                  ('RA01 Antalya', -60, 'Turkey')):
                s = today - dt.timedelta(days=back)
                Trip.objects.create(owner=u, name=name, start_date=s,
                                    end_date=s + dt.timedelta(days=3),
                                    countries=c)
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            h = A.get('/travel/?view=list&show=all').content.decode()
            yp = h.split('data-pop="year"')[1].split('</details>')[0]
            ok(yp.count('<a href="?show=all&amp;year=') ==
               len(set([today.year, (today + dt.timedelta(days=60)).year,
                        (today - dt.timedelta(days=20)).year])),
               'THE YEAR DROP-DOWN has its years, each a link', yp[:200])
            ok(h.count('data-compare-pick') == 2 and
               h.count('class="tv-pickcard form-card"') == 2,
               'COMPARE: a tick in each of the two cards')
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            h = M.get('/travel/m/trips/?view=list&show=all').content.decode()
            ok('data-pop="country"' in h and '<select' not in h.split(
                'data-trip-filters')[1].split('</nav>')[0],
               'THE PHONE: the same drop-downs')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. HELP AND REGISTERED')
# ==========================================================================
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('at the foot of two or more trip cards' in adm and
   'press either and its list opens' in adm,
   'HELP: Compare at the foot of the card; the menus open their lists')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
