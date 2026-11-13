# -*- coding: utf-8 -*-
"""test_gift_edit.py - round CG-2, 13 Nov 2026.

RELEASE 78 - EDIT AND DELETE ANY GIFT. Demetri, 12:09: "Can I delete
gifts that I have added to a contact. Maybe delete the gift from 2024?
Or Edit the gift from 2025?" Edit in the contact's Gifts pop-up and on My
gifts; Delete asks first, in both.
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

SUFFIX = '.bak_giftedit'
ME = 'test_gift_edit.py'
PATCHER = 'apply_gift_edit.py'
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
cm = read(J(PT, 'celebration_management.html'))
ok("function editGift(g)" in cm and 'id="gift_action"' in cm and
   "window.confirm('Delete this gift (" in cm,
   'POP-UP: Edit fills the form; Delete asks first')
mg = read(J(PT, 'celebration_gifts.html'))
ok(mg.count('data-gift-edit') == 2 and
   "return confirm('Delete this gift? This cannot be undone.');" in mg,
   'MY GIFTS: Edit and Delete under every gift and every idea')
gv = read(J(ROOT, 'pages', 'views', 'celebration_gifts.py'))
ok("if action == 'edit':" in gv and
   "g = mine.filter(pk=request.POST.get('gift_id')).first()" in gv,
   'THE VIEW: an edit, only ever of your own gift')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('to delete it, which asks first' in hp, 'HELP: says so')

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

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            def perm(code):
                p, _ = Permission.objects.get_or_create(
                    codename=code, content_type__app_label='auth',
                    defaults={'name': code})
                return p
            a = User.objects.create_user('ge_a', 'gea@example.com', 'x')
            b = User.objects.create_user('ge_b', 'geb@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm('can_access_celebrations'))
            ws = ensure_workspace(a)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            for u in (a, b):
                UserProfile.objects.update_or_create(
                    user=u, defaults={'workspace': ws})
            x = Contact.objects.create(name='GE Xena', relationship='friend',
                                       workspace=ws, created_by=a)
            g = Gift.objects.create(owner=a, contact=x, contact_name=x.name,
                                    year=2025, occasion='birthday',
                                    gift='GE scarf', cost=Decimal('40'),
                                    given=True, idea='GE silk scarf')
            url = '/celebrations/gifts/save/'
            r = ca.post(url, {'action': 'edit', 'gift_id': g.pk,
                              'kind': 'given', 'what': 'GE wool scarf',
                              'occasion': 'nameday', 'year': '2024',
                              'amount': '35,50',
                              'next': '/celebrations/gifts/?tab=mine'})
            g.refresh_from_db()
            ok(r.status_code == 302 and
               r['Location'] == '/celebrations/gifts/?tab=mine' and
               g.gift == 'GE wool scarf' and g.year == 2024 and
               g.occasion == 'nameday' and g.cost == Decimal('35.50') and
               g.idea == 'GE silk scarf',
               'EDIT: what, occasion, year, cost - the plan kept; back to '
               'My gifts')
            ca.post(url, {'action': 'edit', 'gift_id': g.pk, 'kind': 'idea',
                          'what': 'GE gloves', 'amount': '20'})
            g.refresh_from_db()
            ok(not g.given and g.idea == 'GE gloves' and g.gift == '' and
               g.cost is None and g.budget == Decimal('20.00'),
               '  turned back into an idea: what was bought is cleared')
            ca.post(url, {'action': 'edit', 'gift_id': g.pk, 'kind': 'idea',
                          'what': '   '})
            g.refresh_from_db()
            ok(g.idea == 'GE gloves', '  an empty name changes nothing')
            cb.post(url, {'action': 'edit', 'gift_id': g.pk,
                          'kind': 'given', 'what': 'GE hacked'})
            g.refresh_from_db()
            ok(g.idea == 'GE gloves' and g.gift == '',
               'PRIVATE: someone else cannot edit it')
            t = ca.get('/celebrations/gifts/').content.decode()
            ok('data-gift-edit' in t and 'GE gloves' in t,
               'MY GIFTS shows it with its Edit')
            ca.post(url, {'action': 'delete', 'gift_id': g.pk})
            ok(not Gift.objects.filter(pk=g.pk).exists(), 'DELETE: gone')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL')
# ==========================================================================
try:
    ok("if action == 'edit':" not in was(J(ROOT, 'pages', 'views',
                                           'celebration_gifts.py')),
       'before this round: a gift could not be edited')
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
