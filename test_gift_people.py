# -*- coding: utf-8 -*-
"""test_gift_people.py - round CG-4, 14 Nov 2026.

RELEASE 80 - MY GIFTS BY PERSON. Demetri, 14 Nov: "wouldn't it make more
sense to consolidate a person (like Aki) instead of having two separate
sections?" Each person once in a year with their total, their gifts under
them with Edit beside each; the gift amounts sit left of the person's
total ("To show that these two added make up the 55"); Given and An idea
are now Bought and Just an idea. The plan is in brackets ("maybe put
the planned: Pants in brackets"). "Bought as planned" on the Christmas
list, and next year's list starts from last year's people.
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

SUFFIX = '.bak_giftpeople'
ME = 'test_gift_people.py'
PATCHER = 'apply_gift_people.py'
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
ok(mg.count('{% for p in y.people %}') == 1 and
   mg.count('{% for p in idea_people %}') == 1,
   'MY GIFTS: each person once, in a year and in Ideas')
ok(mg.count(' <span class="gift-edit-link" title="Edit"><i class="fas fa-pen"') == 2,
   'Edit sits beside the gift, inside its line')
ok('.gift-line .gift-amt { margin-left: auto; margin-right: 96px;' in mg,
   'the gift amounts sit left of the person\'s total')
cm = read(J(PT, 'celebration_management.html'))
ok(mg.count('value="given"{% if g.given %} checked{% endif %}> Bought</label>') == 2 and mg.count('> Just an idea</label>')
   == 2 and '> Bought</label>' in cm and '> Just an idea</label>' in cm and
   "'gift-row-btn gift-mark', 'Mark bought')" in cm and
   '> Given</label>' not in mg + cm,
   'BOUGHT / JUST AN IDEA, in My gifts and in the Gifts pop-up')
gv = read(J(ROOT, 'pages', 'views', 'celebration_gifts.py'))
ok('<span class="text-muted small">(planned: {{ g.idea }})</span>' in mg,
   'the plan in brackets: "Shirt (planned: Pants)"')
ok('data-as-planned> Bought as planned</label>' in mg and
   "tick.disabled = !tick.checked &&" in mg,
   'CHRISTMAS: "Bought as planned" copies and greys; typing greys the tick')
ok('data-xmas-past' in mg and "year__lt=xyear" in gv,
   'CHRISTMAS: each person\'s past Christmases, a tap away')
ok("if action == 'copy_people':" in gv and 'data-xmas-copy' in mg,
   'CHRISTMAS: copy last year\'s people in one tap')
ok("g.given = bool(as_planned or g.gift or g.cost is not None)" in gv,
   '  writing what was bought is buying it - no tick needed')
ok('def by_person(rows, amount):' in gv, 'THE VIEW groups by person')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('each person once, with their gifts under them' in hp and
   '<strong>Just an idea</strong>' in hp, 'HELP: says so')

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
    from pages.views.celebration_gifts import by_person

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            p, _ = Permission.objects.get_or_create(
                codename='can_access_celebrations',
                content_type__app_label='auth',
                defaults={'name': 'can_access_celebrations'})
            a = User.objects.create_user('gp_a', 'gpa@example.com', 'x')
            a.user_permissions.add(p)
            ws = ensure_workspace(a)
            UserProfile.objects.update_or_create(user=a,
                                                 defaults={'workspace': ws})
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            mk = lambda n: Contact.objects.create(          # noqa: E731
                name=n, relationship='friend', workspace=ws, created_by=a)
            aki, zed = mk('GP Aki'), mk('GP Zed')

            def G(c, **kw):
                return Gift.objects.create(owner=a, contact=c,
                                           contact_name=c.name, **kw)
            G(zed, year=2026, occasion='christmas', gift='GP socks',
              given=True)
            G(aki, year=2026, occasion='birthday', gift='GP yyy',
              cost=Decimal('50'), given=True)
            G(aki, year=2026, occasion='christmas', gift='GP shirt',
              cost=Decimal('5'), given=True)
            G(aki, year=2025, occasion='christmas', gift='GP tie',
              cost=Decimal('9'), given=True)
            G(aki, year=2027, occasion='nameday', idea='GP book',
              budget=Decimal('25'))
            rows = list(Gift.objects.filter(owner=a, given=True, year=2026))
            ppl = by_person(rows, lambda g: g.cost)
            ok([x['who'] for x in ppl] == ['GP Aki', 'GP Zed'] and
               [len(x['rows']) for x in ppl] == [2, 1],
               'BY PERSON: Aki once, with both gifts; people by name')
            ok(ppl[0]['total'] == Decimal('55') and ppl[1]['total'] is None,
               '  each with their total; none when no gift has an amount')
            h = ca.get('/celebrations/gifts/').content.decode()
            y26 = h[h.index('>2026<'):h.index('>2025<')]
            ok(y26.count('data-gift-person') == 2 and
               y26.count('GP Aki') == 1 and y26.count('data-gift-edit') == 3
               and '€55' in y26,
               'THE PAGE: in 2026 Aki is one person with two gifts and €55')
            ok(h.count('data-gift-person') == 3 and 'data-ideas-nudge' in h,
               '  2025 is its own year; the idea waits on the Ideas tab')
            hi = ca.get('/celebrations/gifts/?tab=ideas').content.decode()
            ok(hi.count('data-gift-person') == 1 and 'GP book' in hi,
               '  and the Ideas tab groups it by person')
            # BOUGHT AS PLANNED, and buying by writing it down
            r1 = G(aki, year=2030, occasion='christmas', idea='GP pants',
                   budget=Decimal('10'))
            r2 = G(zed, year=2030, occasion='christmas', idea='GP hat',
                   budget=Decimal('12'))
            u = '/celebrations/gifts/'
            ca.post(u, {'action': 'save_row', 'tab': 'christmas',
                        'year': 2030, 'gift_id': r1.pk, 'idea': 'GP pants',
                        'budget': '10', 'gift': 'GP shirt', 'cost': '5'})
            ca.post(u, {'action': 'save_row', 'tab': 'christmas',
                        'year': 2030, 'gift_id': r2.pk, 'idea': 'GP hat',
                        'budget': '12', 'as_planned': '1'})
            r1.refresh_from_db()
            r2.refresh_from_db()
            ok(r1.given and r1.gift == 'GP shirt' and
               r1.cost == Decimal('5.00') and r1.idea == 'GP pants',
               'WRITTEN DOWN: bought, no tick - the plan kept')
            ok(r2.given and r2.gift == 'GP hat' and
               r2.cost == Decimal('12.00'),
               'BOUGHT AS PLANNED: the plan and budget copied across')
            h = ca.get(u + '?tab=christmas&year=2030').content.decode()
            f1 = h[h.index('id="gift-%d"' % r1.pk):]
            f1 = f1[:f1.index('</form>')]
            f2 = h[h.index('id="gift-%d"' % r2.pk):]
            f2 = f2[:f2.index('</form>')]
            ok(' disabled data-as-planned>' in f1 and 'readonly' not in f1,
               '  a different gift opens with the tick greyed out')
            ok(' checked data-as-planned>' in f2 and f2.count(' readonly') == 2,
               '  as planned opens ticked, its two boxes greyed')
            ca.post(u, {'action': 'save_row', 'tab': 'christmas',
                        'year': 2030, 'gift_id': r2.pk, 'idea': 'GP hat',
                        'budget': '12', 'gift': '', 'cost': ''})
            r2.refresh_from_db()
            ok(not r2.given and r2.gift == '' and r2.cost is None,
               'CLEARED: back to just a plan')
            # PAST CHRISTMASES, per person on the list
            G(zed, year=2028, occasion='christmas', gift='GP gloves',
              given=True)
            G(zed, year=2029, occasion='christmas', idea='GP plan only')
            h = ca.get(u + '?tab=christmas&year=2030').content.decode()
            fz = h[h.index('id="gift-%d"' % r2.pk):]
            fz = fz[:fz.index('</form>')]
            fa = h[h.index('id="gift-%d"' % r1.pk):]
            fa = fa[:fa.index('</form>')]
            ok('Past Christmases (2)' in fz and
               '<th scope="col">Year</th><th scope="col">Planned</th>'
               '<th scope="col">Bought</th>' in fz and
               fz.index('<th scope="row">2028</th>') <
               fz.index('<th scope="row">2026</th>') and
               'GP plan only' not in fz,
               'PAST CHRISTMASES: Year, Planned, Bought - newest first, '
               'bought only')
            ok('<th scope="row">2026</th><td><span class="xmas-past-none">'
               '-</span></td><td>GP socks</td>' in fz,
               '  no plan that year: a "-"')
            ok('<th scope="row">2030</th>' not in fa and
               'Past Christmases (2)' in fa and
               '<th scope="row">2026</th>' in fa and 'GP yyy' not in fa,
               '  only Christmas before this one - not a birthday')
            # COPY LAST YEAR'S PEOPLE
            yo = Gift.objects.filter(owner=a, occasion='christmas')
            h = ca.get(u + '?tab=christmas&year=2031').content.decode()
            ok('data-xmas-copy' in h and 'Copy the people from 2030' in h
               and '>2 people from 2030' in h.replace('</span>', ''),
               'NEW YEAR: offers to copy 2030\'s two people')
            G(aki, year=2031, occasion='christmas', idea='GP kept')
            ca.post(u, {'action': 'copy_people', 'tab': 'christmas',
                        'year': 2031})
            got = sorted((g.contact_name, g.idea, g.budget, g.given)
                         for g in yo.filter(year=2031))
            ok(got == [('GP Aki', 'GP kept', None, False),
                       ('GP Zed', '', None, False)],
               '  copies the people only; Aki already on is left as he was',
               got)
            h = ca.get(u + '?tab=christmas&year=2031').content.decode()
            ok('data-xmas-copy' not in h, '  and then stops offering')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL')
# ==========================================================================
try:
    ok('def by_person(rows, amount):' not in was(
        J(ROOT, 'pages', 'views', 'celebration_gifts.py')),
       'before this round: a row per gift')
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
