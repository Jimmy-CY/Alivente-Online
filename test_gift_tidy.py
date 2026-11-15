# -*- coding: utf-8 -*-
"""test_gift_tidy.py - round CG-5, 15 Nov 2026.

RELEASE 81 - THE GIFTS PAGES TIDIED, from Demetri's run-through on 15 Nov:
the Gifts pop-up has the form on top and "Gifts so far" closed under it,
every gift tagged Bought or Idea, "Mark bought" for an idea, a pencil for
Edit throughout; My gifts tighter and narrower with the occasion as a tag
and Ideas on their own tab; the Christmas table tinted for this year,
banded on hover, with this year's plans marked; the Past Christmases card
tidied and easy to close.
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

SUFFIX = '.bak_gifttidy'
ME = 'test_gift_tidy.py'
PATCHER = 'apply_gift_tidy.py'
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
head('1. THE GIFTS POP-UP')
# ==========================================================================
cm = read(J(PT, 'celebration_management.html'))
f, d = cm.index('id="giftForm"'), cm.index('id="giftPast"')
ok(f < d and '<ul class="gift-list" id="giftList"></ul>' in
   cm[d:d + 400], 'the form first; the gifts so far under it')
ok("past.open = back && q.get('list') === '1';" in cm,
   '  closed, unless coming back from changing one')
ok('id="giftSaved"' in cm and "q.get('saved') === '1'" in cm,
   '  "Saved." after adding')
ok("g.given ? 'Bought' : 'Idea'" in cm and
   "'gift-row-btn gift-mark', 'Mark bought'" in cm,
   'every gift tagged Bought or Idea; an idea has "Mark bought"')
ok("ed.appendChild(el('i', 'fas fa-pen'));" in cm and
   "el('button', 'gift-row-btn', 'Edit')" not in cm, 'a pencil for Edit')

# ==========================================================================
head('2. MY GIFTS AND IDEAS')
# ==========================================================================
mg = read(J(PT, 'celebration_gifts.html'))
ok(mg.count('<span class="gift-occ gift-occ-{{ g.occasion }}">') == 2,
   'the occasion is a tag, on gifts and on ideas')
ok('.gift-person { padding: 2px 0;' in mg and
   '.gift-year { margin-bottom: 30px; max-width: 760px; }' in mg,
   'tighter between people, the year gap kept, narrower')
ok("{% elif tab == 'ideas' %}" in mg and 'data-ideas-nudge' in mg and
   'gift-tab-count' in mg, 'IDEAS: a tab with a count, and a line on '
   'My gifts pointing to it')
ok('<span class="gift-edit-link">Edit</span>' not in mg and
   mg.count('<i class="fas fa-pen" aria-hidden="true"></i><span '
            'class="sr-only">Edit</span>') == 2, 'a pencil for Edit here too')

# ==========================================================================
head('3. THE CHRISTMAS TABLE AND PAST CHRISTMASES')
# ==========================================================================
ok('.xt-table .xt-now {' in mg and '.xt-table tbody tr:hover td' in mg and
   'class="xt-plan' in mg and 'xt-key' in mg,
   'TABLE: this year tinted, the row banded, plans marked with a key')
gv = read(J(ROOT, 'pages', 'views', 'celebration_gifts.py'))
ok("cells.append({'text': ' \\u00b7 '.join(p), 'planned': True})" in gv,
   '  a plan shows only where nothing was bought')
ok('class="xmas-past-card"' in mg and 'data-past-close' in mg and
   "e.key === 'Escape'" in mg, 'PAST CHRISTMASES: a titled card that '
   'closes on x, outside, or Esc')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('<strong>Gifts so far</strong>' in hp and
   'own <strong>Ideas</strong> tab' in hp and 'lightbulb' in hp,
   'HELP: says so')

# ==========================================================================
head('4. DRIVEN')
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
    from pages.models import Contact, Gift, UserProfile
    connection.ensure_connection()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 4 (database)', str(_e).split('\n')[0][:70])
if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from pages.workspace import ensure_workspace

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            p, _ = Permission.objects.get_or_create(
                codename='can_access_celebrations',
                content_type__app_label='auth',
                defaults={'name': 'can_access_celebrations'})
            a = User.objects.create_user('gt_a', 'gta@example.com', 'x')
            a.user_permissions.add(p)
            ws = ensure_workspace(a)
            UserProfile.objects.update_or_create(user=a,
                                                 defaults={'workspace': ws})
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
            c = Contact.objects.create(name='GT Ivy', relationship='friend',
                                       workspace=ws, created_by=a)
            Gift.objects.create(owner=a, contact=c, contact_name=c.name,
                                year=2026, occasion='birthday',
                                idea='GT lamp')
            Gift.objects.create(owner=a, contact=c, contact_name=c.name,
                                year=2025, occasion='nameday',
                                gift='GT pen', given=True)
            h = ca.get('/celebrations/gifts/').content.decode()
            ok('GT pen' in h and 'GT lamp' not in h and
               '1 idea still to use' in h and 'gift-occ-nameday' in h,
               'MY GIFTS: bought only, the occasion tagged, pointing to '
               'the idea')
            h = ca.get('/celebrations/gifts/?tab=ideas').content.decode()
            ok('data-gifts-ideas' in h and 'GT lamp' in h and
               'GT pen' not in h and 'aria-current="page">Ideas' in h,
               'IDEAS: on their own tab')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('5. CONTROL AND REGISTERED')
# ==========================================================================
try:
    ok('id="giftPast"' not in was(J(PT, 'celebration_management.html')),
       'before this round: the list came first, open')
except IOError as _e:
    skip('control', str(_e))
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
