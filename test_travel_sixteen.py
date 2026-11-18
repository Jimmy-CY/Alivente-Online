# -*- coding: utf-8 -*-
"""test_travel_sixteen.py - round TR-16, 18 Nov 2026.

RELEASE 100 - TRAVEL: TIDIER TRIP FILTERS.
Demetri, 18 Nov: "I don't like how the 1 is placed near the Upcoming and
the Past. It look like part of the name. We need to differentiate it.
Also, Can we put the "All" first on the left. What happens when we have
additional years and countries. Are our filters not going to look messy?
Is there not a cleverer way to do years and countries? We leave All,
Upcoming and Past as is." - "Yes. Let's go ahead and build it."
All, Upcoming and Past as chips, All first, each count a badge; Year and
Country as menus; they combine; the phone the same.
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

SUFFIX = '.bak_travel16'
ME = 'test_travel_sixteen.py'
PATCHER = 'apply_travel_sixteen.py'
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
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from travel import trip_filter as TF                        # noqa: E402

# ==========================================================================
head('1. THE RULES (no database)')
# ==========================================================================


class Req(object):
    def __init__(self, **g):
        self.GET = g


class T(object):
    def __init__(self, name, start, end, where):
        self.name, self.start, self.end = name, start, end
        self.where_list = where


D = dt.date
TODAY = D(2026, 11, 18)
rows = [T('Athens Nov', D(2026, 11, 3), D(2026, 11, 11), ['Greece',
                                                          'Ireland']),
        T('Anniversary', D(2027, 1, 28), D(2027, 1, 31), ['Turkey']),
        T('Crete', D(2026, 6, 1), D(2026, 6, 8), ['Greece']),
        T('Rhodes', D(2025, 8, 1), D(2025, 8, 9), ['Greece']),
        T('Someday', None, None, [])]
ok(TF.read(Req()) == ('upcoming', '', ''),
   'NOTHING ASKED: Upcoming, any year, any country')
ok(TF.read(Req(show='2026')) == ('all', '2026', '') and
   TF.read(Req(show='c:Greece')) == ('all', '', 'Greece') and
   TF.read(Req(show='nonsense', year='x')) == ('all', '', ''),
   'OLD LINKS still work: ?show=2026 and ?show=c:Greece')
F = TF.apply(Req(show='all'), rows, TODAY)
ok([t.name for t in F['trips']] == ['Someday', 'Anniversary', 'Athens Nov',
                                    'Crete', 'Rhodes'],
   'ALL: every trip, the latest first (undated newest of all)')
ok((F['n_all'], F['n_upcoming'], F['n_past']) == (5, 2, 3),
   '  the badges: 5, 2 upcoming, 3 past')
ok(F['years'] == [(2027, 1), (2026, 2), (2025, 1)],
   'THE YEAR MENU: newest first, with how many', F['years'])
ok(F['countries'] == [('Greece', 3), ('Ireland', 1), ('Turkey', 1)],
   'THE COUNTRY MENU: most trips first, then by name', F['countries'])
F = TF.apply(Req(show='past', year='2026', country='greece'), rows, TODAY)
ok([t.name for t in F['trips']] == ['Athens Nov', 'Crete'] and
   F['country_name'] == 'Greece',
   'THEY COMBINE: Past + 2026 + Greece (any letter case)')
ok((F['n_all'], F['n_upcoming'], F['n_past']) == (2, 0, 2),
   '  and the badges follow what is picked')
ok(F['link_all'] == '?show=all&year=2026&country=greece' and
   F['clear_year'] == '?show=past&country=greece' and
   F['clear_country'] == '?show=past&year=2026',
   '  each chip keeps the others; each x clears only its own')
F = TF.apply(Req(country='Ireland'), rows, TODAY)
ok(F['auto_past'] and [t.name for t in F['trips']] == ['Athens Nov'],
   'NOTHING AHEAD THERE: the past trips to that country, said so')
inc = read(J(TT, '_trip_filters.html'))
ok(inc.index('data-chip="all"') < inc.index('data-chip="upcoming"') <
   inc.index('data-chip="past"') < inc.index('data-menu="year"') <
   inc.index('data-menu="country"'),
   'THE ORDER: All, Upcoming, Past, then Year and Country')
ok('class="tv-count"' in inc and 'tv-sub' not in inc,
   'THE COUNT is its own badge, not grey text after the name')
for f in ('trips.html', J('m', 'trips.html')):
    ok("{% include 'travel/_trip_filters.html'" in read(J(TT, f)),
       '  %s uses them' % f)
css = read(J(TT, '_style.html')) + read(J(TA, 'assets', 'travel.css'))
ok(css.count('.tv-count {') >= 2 and css.count('.tv-picked {') >= 2,
   '  styled on the computer and the phone')
ph = read(J(TA, 'phone.py'))
# RA01, 18 Nov 2026 - tv16-1 or later (it moves with every new look).
_v = re.search(r"SW_VERSION = 'tv(\d+)-(\d+)'", ph)
ok(_v and int(_v.group(1)) >= 16 and
   read(J(TT, 'm', 'base.html')).count('?v=tv%s-%s' % _v.groups()) == 2,
   'THE PHONE APP fetches the new look (tv16-1 or later)')
try:
    ok('Upcoming <span class="tv-sub">' in was(J(TT, 'trips.html')),
       'CONTROL: before this round the count sat after the name')
except IOError as _e:
    skip('control', str(_e))

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
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
            u = User.objects.create_user('tv16a', 'tv16a@example.com', 'x')
            u.user_permissions.add(perm)
            UserProfile.objects.update_or_create(
                user=u, defaults={'workspace': ensure_workspace(u)})
            today = timezone.localdate()
            for name, back, c in (('TV16 Athens', 20, 'Greece'),
                                  ('TV16 Crete', 200, 'Greece'),
                                  ('TV16 Antalya', -60, 'Turkey')):
                s = today - dt.timedelta(days=back)
                Trip.objects.create(owner=u, name=name, start_date=s,
                                    end_date=s + dt.timedelta(days=3),
                                    countries=c)
            A = Client(SERVER_NAME='localhost')
            A.force_login(u)
            h = A.get('/travel/?view=list&show=all').content.decode()
            ok('data-trip-filters' in h and
               'All <span class="tv-count" aria-label="3 trips">3</span>' in h
               and 'data-menu="year"' in h and 'data-menu="country"' in h,
               'THE COMPUTER: All 3 in a badge, and the two menus')
            # RA01 - our own drop-down: Greece first, with its count.
            pop = h.split('data-pop="country"')[1].split('</div></details>')[0]
            ok(pop.index('Greece') < pop.index('Turkey') and
               'country=Greece">Greece <span class="tv-count" '
               'aria-label="2 trips">2</span>' in pop,
               '  Greece first in the Country menu, with its 2 trips')
            h = A.get('/travel/?view=list&show=past&country=Greece'
                      ).content.decode()
            ok('TV16 Athens' in h and 'TV16 Crete' in h and
               'TV16 Antalya' not in h and 'data-picked="country"' in h and
               'data-menu="country"' not in h,
               'PAST + GREECE: just those, and Greece shows as a chip with x')
            M = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            M.force_login(u)
            h = M.get('/travel/m/trips/?view=list&show=all&country=Turkey'
                      ).content.decode()
            ok('TV16 Antalya' in h and 'TV16 Athens' not in h and
               'data-picked="country"' in h and 'class="tv-count"' in h,
               'THE PHONE: the same chips and menus, and they work')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. HELP AND REGISTERED')
# ==========================================================================
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('two menus: <strong>Year</strong>' in adm and 'They combine' in adm,
   'HELP on the computer: the badges, the menus, and that they combine')
ok('the Year and Country menus' in read(J(TT, 'm', 'help.html')),
   '  and on the phone')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
