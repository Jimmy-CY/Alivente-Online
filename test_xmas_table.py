# -*- coding: utf-8 -*-
"""test_xmas_table.py - round CG-3, 14 Nov 2026.

RELEASE 79 - THE CHRISTMAS LIST AS A TABLE. Demetri, 14 Nov: "I want to
retain this view, but I also want to have a view which is a table. The
columns are the latest year on the left ... to the first year that a gift
was captured. It must be scrollable. Then the rows must be all of the
people that I have personally captured Christmas gifts for ... insert
'-' ... I just want to show What We Bought. No Budget, No Plan, No Cost."
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

SUFFIX = '.bak_xmastable'
ME = 'test_xmas_table.py'
PATCHER = 'apply_xmas_table.py'
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
PT = J(ROOT, 'pages', 'templates')

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
mg = read(J(PT, 'celebration_gifts.html'))
ok('aria-label="Christmas view"' in mg and
   '?tab=christmas&amp;view=table' in mg,
   'A List / Table switch on the Christmas list - the list is kept')
ok('<table class="alv-matrix xt-table">' in mg and
   'class="alv-matrix-scroll xt-scroll"' in mg,
   'THE TABLE is the house matrix: it scrolls, the names stay put')
ok('<td class="alv-matrix-absent">-</td>' in mg, 'a gap is "-"')
gv = read(J(ROOT, 'pages', 'views', 'celebration_gifts.py'))
ok('def christmas_table(mine):' in gv and
   'cols = list(range(max(years), min(years) - 1, -1))' in gv,
   'THE VIEW: newest year first, down to the first')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('to see every Christmas at once' in hp, 'HELP: says so')

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from decimal import Decimal                                 # noqa: E402
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from pages.models import Contact, Gift, UserProfile
    connection.ensure_connection()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace
    from pages.views.celebration_gifts import christmas_table

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            def perm(code):
                p, _ = Permission.objects.get_or_create(
                    codename=code, content_type__app_label='auth',
                    defaults={'name': code})
                return p
            a = User.objects.create_user('xt_a', 'xta@example.com', 'x')
            b = User.objects.create_user('xt_b', 'xtb@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm('can_access_celebrations'))
            ws = ensure_workspace(a)
            for u in (a, b):
                UserProfile.objects.update_or_create(
                    user=u, defaults={'workspace': ws})
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            mk = lambda n: Contact.objects.create(          # noqa: E731
                name=n, relationship='friend', workspace=ws, created_by=a)
            zoe, bob, ann = mk('XT Zoe'), mk('XT Bob'), mk('XT Ann')

            def G(owner, c, year, **kw):
                return Gift.objects.create(owner=owner, contact=c,
                                           contact_name=c.name, year=year,
                                           occasion='christmas', **kw)
            G(a, zoe, 2026, idea='XT plan only', budget=Decimal('50'))
            G(a, zoe, 2025, gift='XT watch', cost=Decimal('90'),
              idea='XT a book', budget=Decimal('30'), given=True)
            G(a, zoe, 2022, gift='XT scarf', given=True)
            G(a, zoe, 2022, gift='XT gloves', given=True)
            G(a, bob, 2024, idea='XT perfume', given=True)
            G(a, ann, 2026, idea='XT only an idea')
            Gift.objects.create(owner=a, contact=bob, contact_name=bob.name,
                                year=2023, occasion='birthday',
                                gift='XT birthday cake', given=True)
            G(b, bob, 2021, gift='XT someone else', given=True)

            t = christmas_table(Gift.objects.filter(owner=a))
            ok(t['xt_years'] == [2025, 2024, 2023, 2022],
               'COLUMNS: the latest year bought for, down to the first - '
               'gaps included', t['xt_years'])
            names = [r['who'] for r in t['xt_rows']]
            ok(names == ['XT Bob', 'XT Zoe'],
               'ROWS: people with a Christmas gift bought, by name - not '
               'someone with only a plan', names)
            zr = t['xt_rows'][1]['cells']
            ok(zr == ['XT watch', '', '', 'XT scarf · XT gloves'],
               'CELLS: what was bought - not the plan; two in a year share '
               'the cell', zr)
            ok(t['xt_rows'][0]['cells'] == ['', 'XT perfume', '', ''],
               '  ticked Bought with only the plan written: the plan is '
               'what was bought; a birthday gift is not here')
            bob.delete()
            t = christmas_table(Gift.objects.filter(owner=a))
            ok(t['xt_rows'][0]['who'] == 'XT Bob' and t['xt_rows'][0]['gone'],
               'A DELETED CONTACT keeps their row')
            ok(christmas_table(Gift.objects.none()) ==
               {'xt_years': [], 'xt_rows': []}, 'NOTHING BOUGHT: an empty '
               'table, not an error')

            r = ca.get('/celebrations/gifts/?tab=christmas&view=table')
            h = r.content.decode()
            ok(r.status_code == 200 and 'data-xmas-table' in h and
               'XT watch' in h and '<th scope="col">2025</th>' in h,
               'THE PAGE draws the table')
            ok('XT plan only' not in h and '90' not in
               h[h.index('data-xmas-table'):h.index('</table>')] and
               'XT someone else' not in h and 'data-shopping-list' not in h,
               '  no plan, no budget, no cost; nobody else\'s gifts; no '
               'shopping list button')
            ok(h.count('<td class="alv-matrix-absent">-</td>') == 5,
               '  every empty year is a "-"')
            r = ca.get('/celebrations/gifts/?tab=christmas&year=2026')
            h = r.content.decode()
            ok('data-xmas-row' in h and 'data-xmas-table' not in h and
               'data-shopping-list' in h,
               'THE LIST is still there, as it was')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL')
# ==========================================================================
try:
    ok('def christmas_table(mine):' not in was(
        J(ROOT, 'pages', 'views', 'celebration_gifts.py')),
       'before this round: no table')
except IOError as _e:
    skip('section 3', str(_e))

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
