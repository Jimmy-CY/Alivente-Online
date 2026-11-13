# -*- coding: utf-8 -*-
"""test_gifts.py - rounds BV-1 and CG-1, 13 Nov 2026.

RELEASES 74 AND 75, ONE BUNDLE (and PT-3: At home today joins Your
sections in Wellness Settings, switched per person).
  R74 (BV-1): Recipe management no longer sends every recipe for the book
      on every visit - the book fetches them (?book=1) when it opens.
  R75 (CG-1): gifts. Private to whoever records them; on "my own"
      celebrations only; never lost (kept with the name if the contact is
      deleted, a warning before taking yourself off); My gifts; the
      Christmas list (plan, then buy - they may differ - planned against
      spent, the shopping list to himself on WhatsApp); and a greeting
      written by Claude, opened in WhatsApp.
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

SUFFIX = '.bak_gifts'
ME = 'test_gifts.py'
PATCHER = 'apply_gifts.py'
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
rm = read(J(PT, 'recipe_management.html'))
rc = read(J(ROOT, 'pages', 'views', 'recipes', 'recipe_crud.py'))
ok('all_recipes_for_book' not in rm and
   'loadBookRecipes().then(renderBookSpread)' in rm and
   "q.set('book', '1')" in rm,
   'BOOK: the page no longer carries every recipe; the book fetches them')
ok("if request.GET.get('book') == '1':" in rc and
   "'all_recipes_for_book': json.dumps" not in rc,
   '  and the view answers ?book=1 with them, and builds them only then')
m = read(J(ROOT, 'pages', 'models.py'))
ok('class Gift(models.Model):' in m and
   'on_delete=models.SET_NULL' in m[m.index('class Gift('):] and
   "db_table = 'celebration_gifts'" in m,
   'GIFT: its own table; the contact may go and the gift stays')
gv = read(J(ROOT, 'pages', 'views', 'celebration_gifts.py'))
ok(gv.count('Gift.objects.filter(owner=') >= 3 and
   'mine = Gift.objects.filter(owner=request.user)' in gv,
   '  every read is filtered by owner')
cm = read(J(PT, 'celebration_management.html'))
ok('{% if contact.is_mine %}' in cm and '{% if event.is_mine %}' in cm and
   'data-gift-open' in cm and 'data-greet' in cm,
   'CELEBRATIONS: Gifts and Greeting only on my own celebrations')
ok('id="giftKeepModal"' in cm and 'modal-footer' not in
   cm[cm.index('id="giftModal"'):cm.index('<!-- Import Modal -->')],
   '  the warning pop-up; the new pop-ups add no modal-footer')
ok(os.path.isfile(J(PT, 'celebration_gifts.html')),
   'MY GIFTS: its own page, with the Christmas list as a tab')
mig = J(ROOT, 'pages', 'migrations', '0119_celebration_gifts.py')
ok(os.path.isfile(mig) and 'migrations.CreateModel' in read(mig) and
   read(mig).count('migrations.') == 3,
   'MIGRATION 0119: one CreateModel, nothing else',
   'run python manage.py migrate before pushing')
st = read(J(ROOT, 'wellness', 'templates', 'wellness', 'settings.html'))
ok(st.index('data-home-switch') < st.index('Save my sections') and
   st.count('data-home-switch') == 1,
   'SETTINGS: At home today is a row in Your sections, and only there')
hp = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('data-tab-slug="cel-gifts"' in hp and 'Christmas list' in hp and
   'Open in WhatsApp' in hp, 'HELP: a Gifts tab in Celebrations')

# ==========================================================================
head('2. SMALL RULES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from decimal import Decimal                                 # noqa: E402
import importlib                                            # noqa: E402
CG = importlib.import_module('pages.views.celebration_gifts')
ok(CG.money('25') == Decimal('25.00') and CG.money('€45,5') ==
   Decimal('45.50') and CG.money('') is None and CG.money('abc') is None,
   'amounts: 25, EUR 45,5, nothing, nonsense')
ok(CG.wa_number('99 123456') == '35799123456' and
   CG.wa_number('+44 7700 900123') == '447700900123' and
   CG.wa_number('0030 6912345678') == '306912345678' and
   CG.wa_number('') == '', 'WhatsApp numbers: Cypriot local, +44, 00 30')

class _G(object):
    def __init__(self, who, idea, budget):
        self.who, self.idea, self.budget = who, idea, budget
t = CG.shopping_text(2026, [_G('Eleni', 'Scarf', Decimal('60')),
                            _G('Nico', '', None)])
ok('Christmas 2026 - still to buy (2)' in t and 'Eleni - Scarf - €60' in t
   and '- Nico' in t and 'Budget: €60' in t, 'the shopping list reads right')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from pages.models import (HouseholdMember, Contact, CelebrationEvent,
                              Gift, UserProfile)
    connection.ensure_connection()
    Gift.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

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
            a = User.objects.create_user('cg_a', 'cga@example.com', 'x')
            b = User.objects.create_user('cg_b', 'cgb@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm('can_access_celebrations'),
                                       perm('can_edit_celebrations'),
                                       perm('can_access_recipes'))
            ws = ensure_workspace(a)
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            # After logging in: login saves the user, and the user's saved
            # profile (cached, workspace empty) would undo this otherwise.
            for u in (a, b):
                UserProfile.objects.update_or_create(
                    user=u, defaults={'workspace': ws})
            day = timezone.localdate()
            ma = HouseholdMember.objects.create(workspace=ws, name='CG Al',
                                                user=a)
            mb = HouseholdMember.objects.create(workspace=ws, name='CG Bo',
                                                user=b)
            x = Contact.objects.create(name='CG Xena', relationship='friend',
                                       phone='99 123456', workspace=ws,
                                       created_by=a)
            y = Contact.objects.create(name='CG Yannis', relationship='family',
                                       workspace=ws, created_by=a)
            ev = CelebrationEvent.objects.create(
                contact=x, event_type='birthday', created_by=a,
                event_date=day.replace(year=day.year - 40))
            ev.relevant_to.add(ma)
            ev2 = CelebrationEvent.objects.create(
                contact=y, event_type='nameday', created_by=a,
                event_date=day.replace(year=1900))
            ev2.relevant_to.add(mb)

            r = ca.post('/celebrations/gifts/save/', {
                'action': 'add', 'contact_id': x.pk, 'kind': 'given',
                'what': 'CG silver bracelet', 'occasion': 'birthday',
                'year': day.year - 1, 'amount': '120',
                'next': '/celebrations/contacts/?gifts=%d' % x.pk})
            g = Gift.objects.filter(owner=a, contact=x).first()
            ok(r.status_code == 302 and g and g.given and
               g.cost == Decimal('120.00') and g.contact_name == 'CG Xena',
               'GIFT: Al records one for Xena; it keeps her name')
            ok(r['Location'].startswith('/celebrations/contacts/?gifts='),
               '  and lands back on the pop-up')
            r = ca.post('/celebrations/gifts/save/', {
                'action': 'add', 'contact_id': x.pk, 'kind': 'given',
                'what': 'x', 'next': 'https://example.com/'})
            ok(r['Location'] == '/celebrations/contacts/',
               '  a "next" that is not ours goes to Celebrations')
            Gift.objects.filter(owner=a, gift='x').delete()

            t = ca.get('/celebrations/contacts/').content.decode()
            ok('data-gift-open="%d"' % x.pk in t and
               'data-gift-open="%d"' % y.pk not in t and
               'CG silver bracelet' in t and
               'data-greet="%d"' % ev.pk in t,
               'CELEBRATIONS: Al gets Gifts and Greeting on Xena (his), not '
               'Yannis (Bo\'s)')
            t = cb.get('/celebrations/contacts/').content.decode()
            ok('CG silver bracelet' not in t and
               'data-gift-open="%d"' % x.pk not in t and
               'data-gift-open="%d"' % y.pk in t,
               '  Bo sees none of Al\'s gifts - only his own Yannis')
            cb.post('/celebrations/gifts/save/', {'action': 'delete',
                                                  'gift_id': g.pk})
            ok(Gift.objects.filter(pk=g.pk).exists(),
               'PRIVATE: Bo cannot delete Al\'s gift')
            t = cb.get('/celebrations/gifts/').content.decode()
            ok('CG silver bracelet' not in t, '  nor see it in My gifts')
            t = ca.get('/celebrations/gifts/').content.decode()
            ok('CG silver bracelet' in t and str(day.year - 1) in t and
               'Spent €120' in t, 'MY GIFTS: Al\'s, by year, with the total')

            # THE CHRISTMAS LIST
            yr = day.year
            ca.post('/celebrations/gifts/', {
                'action': 'add_people', 'tab': 'christmas', 'year': yr,
                'contact_ids': [x.pk, y.pk]})
            ca.post('/celebrations/gifts/', {
                'action': 'add_people', 'tab': 'christmas', 'year': yr,
                'contact_ids': [x.pk]})
            rows = list(Gift.objects.filter(owner=a, occasion='christmas',
                                            year=yr).order_by('contact_name'))
            ok(len(rows) == 2, 'CHRISTMAS: tick two people, both added once')
            rx, ry = rows
            ca.post('/celebrations/gifts/', {
                'action': 'save_row', 'tab': 'christmas', 'year': yr,
                'gift_id': rx.pk, 'idea': 'CG scarf', 'budget': '60',
                'gift': 'CG perfume', 'cost': '45,50', 'given': '1'})
            ca.post('/celebrations/gifts/', {
                'action': 'save_row', 'tab': 'christmas', 'year': yr,
                'gift_id': ry.pk, 'idea': 'CG book', 'budget': '25'})
            rx.refresh_from_db()
            ok(rx.idea == 'CG scarf' and rx.gift == 'CG perfume' and
               rx.cost == Decimal('45.50') and rx.given,
               '  planned a scarf, bought perfume - both kept')
            t = ca.get('/celebrations/gifts/?tab=christmas&year=%d'
                       % yr).content.decode()
            ok('€85' in t and '€45.50' in t and '1 of 2' in t,
               '  planned EUR 85 against spent EUR 45.50; one still to buy')
            import re as _re
            from urllib.parse import unquote
            link = unquote(_re.search(r'href="(https://wa\.me/\?text=[^"]+)"',
                                      t).group(1).replace('&amp;', '&'))
            ok('CG Yannis - CG book - €25' in link and 'CG Xena' not in link,
               '  the WhatsApp list has who is left to buy for, not Xena')
            cb.post('/celebrations/gifts/', {
                'action': 'remove_row', 'tab': 'christmas', 'year': yr,
                'gift_id': ry.pk})
            ok(Gift.objects.filter(pk=ry.pk).exists(),
               '  Bo cannot take people off Al\'s list')

            # GREETING - Claude is not called here; its answer is stood in.
            real = CG.ask_greeting
            CG.ask_greeting = lambda prompt, client=None: (
                'Happy birthday Xena!' if 'They turn 40.' in prompt else None)
            try:
                r = ca.post('/celebrations/event/%d/greeting/' % ev.pk,
                            {'language': 'English'})
                d = r.json()
                ok(r.status_code == 200 and d['text'] ==
                   'Happy birthday Xena!' and d['number'] == '35799123456',
                   'GREETING: written for her 40th; her WhatsApp number')
                r = cb.post('/celebrations/event/%d/greeting/' % ev.pk)
                ok(r.status_code == 404, '  not for someone else\'s '
                   'celebration')
            finally:
                CG.ask_greeting = real

            # NEVER LOST
            Gift.objects.create(owner=b, contact=x, contact_name='CG Xena',
                                year=yr, occasion='birthday', idea='CG mug')
            r = ca.post('/celebrations/contacts/', {
                'action': 'delete_contact', 'contact_id': x.pk})
            kept = list(Gift.objects.filter(contact_name='CG Xena'))
            ok(len(kept) == 3 and all(k.contact_id is None for k in kept),
               'DELETED CONTACT: all three gift records survive, with the '
               'name')
            ok(Gift.objects.get(owner=b, idea='CG mug').orphan_told is False
               and Gift.objects.filter(owner=a, orphan_told=True).count() == 2,
               '  Al, who deleted her, was told then; Bo not yet')
            t = cb.get('/celebrations/gifts/', follow=True).content.decode()
            ok('CG mug' in t and '(contact deleted)' in t and
               'CG Xena was deleted from Celebrations' in t,
               '  Bo is told on his next visit, and it is in My gifts')
            ok(Gift.objects.get(owner=b, idea='CG mug').orphan_told,
               '  once')

            # PT-3 - At home today is switched in Your sections, per person.
            from wellness.models import WellnessProfile
            a.user_permissions.add(perm('can_access_wellness'))
            WellnessProfile.objects.get_or_create(user=a,
                                                  defaults={'onboarded': True})
            ca.post('/wellness/settings/', {'form': 'sections',
                                            'module': ['habits', 'journal']})
            pa = WellnessProfile.objects.get(user=a)
            ok((pa.prefs or {}).get('home_off') is True,
               'AT HOME TODAY: unticked in Your sections, it is off for Al')
            ca.post('/wellness/settings/', {'weekly_email': '1'})
            pa.refresh_from_db()
            ok((pa.prefs or {}).get('home_off') is True,
               '  and saving the other settings does not switch it back')
            ca.post('/wellness/settings/', {'form': 'sections',
                                            'module': ['habits'],
                                            'home': '1'})
            pa.refresh_from_db()
            t = ca.get('/wellness/settings/').content.decode()
            ok((pa.prefs or {}).get('home_off') is False and
               'At home today' in t[t.index('data-on-names'):
                                    t.index('data-on-names') + 200],
               '  ticked, it is on, and named among the sections switched on')

            # BV-1 - the book
            r = ca.get('/recipe_management/?book=1')
            ok(r.status_code == 200 and r['Content-Type'].startswith(
                'application/json') and isinstance(r.json(), list),
               'BOOK: ?book=1 is the book\'s recipes as JSON')
            t = ca.get('/recipe_management/').content.decode()
            ok('let BOOK_RECIPES = [];' in t, '  the page itself carries '
               'none')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL')
# ==========================================================================
try:
    ok('all_recipes_for_book' in was(J(PT, 'recipe_management.html')) and
       'class Gift(' not in was(J(ROOT, 'pages', 'models.py')),
       'before: the page carried the book; there was no Gift')
except IOError as _e:
    skip('section 4', str(_e))

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# PT-5, 13 Nov 2026 - LL-1 backed celebration_gifts.py up again, so its
# sentinel moved to text that backup does not hold.
ok("Text = 'def greeting_response(request, event_id):'" in gate and
   "Text = 'class Gift(models.Model):'" in gate,
   '  with sentinels on the gifts page and the model')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
