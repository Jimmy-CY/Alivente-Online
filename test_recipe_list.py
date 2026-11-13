# -*- coding: utf-8 -*-
"""test_recipe_list.py - round LL-1, 13 Nov 2026.

RELEASE 77 - RECIPE MANAGEMENT BUILDS THE LIST VIEW ONLY WHEN IT IS USED.
And PT-5: the Wellness greeting and Cooked it ask through Wellness's own
addresses - on a phone the main app's hour had run out, and Demetri's
phone said "Could not reach Claude right now" (13 Nov, 10:55).
Measured on Live, 13 Nov 09:24: 742 KB, of which the list view - the same
48 recipes as the grid, hidden - was 201 KB on every visit.
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

SUFFIX = '.bak_listlazy'
ME = 'test_recipe_list.py'
PATCHER = 'apply_recipe_list.py'
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
ok('<!--list:start-->{% if render_list %}' in rm and
   '{% endif %}<!--list:end-->' in rm,
   'THE LIST: built only when render_list, between two markers')
ok("q.set('part', 'list')" in rm and
   "listView.insertAdjacentHTML('afterbegin', html)" in rm and
   "loadListView();" in rm,
   '  fetched when List is first chosen, its rows put first')
ok("document.cookie = 'recipeView=' + view" in rm,
   '  and the choice kept in a cookie the server reads')
rc = read(J(ROOT, 'pages', 'views', 'recipes', 'recipe_crud.py'))
ok("context['render_list'] = want or request.COOKIES.get('recipeView') == 'list'"
   in rc, 'THE VIEW: the cookie, or ?part=list')

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
    from pages.models import Recipe
    connection.ensure_connection()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            u = User.objects.create_user('ll_a', 'lla@example.com', 'x')
            p, _ = Permission.objects.get_or_create(
                codename='can_access_recipes',
                content_type__app_label='auth',
                defaults={'name': 'can_access_recipes'})
            u.user_permissions.add(p)
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)
            Recipe.objects.create(recipe_name='LL lentil soup', servings=4)
            row = 'class="recipe-list-item"'
            t = c.get('/recipe_management/').content.decode()
            ok(t.count(row) == 1 and 'LL lentil soup' in t and
               'let listLoaded = false;' in t,
               'GRID (the default): no list rows built - only the one the '
               'script writes for Load more')
            r = c.get('/recipe_management/?part=list')
            t = r.content.decode()
            ok(r.status_code == 200 and t.count(row) >= 1 and
               'LL lentil soup' in t and '<html' not in t and
               '<!--list:' not in t,
               '?part=list: the rows alone, not a page')
            c.cookies['recipeView'] = 'list'
            t = c.get('/recipe_management/').content.decode()
            ok(t.count(row) >= 2 and 'let listLoaded = true;' in t,
               'COOKIE says list: built with the page, nothing to fetch')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('2b. PT-5 - ON A PHONE, PAST THE MAIN APP\'S HOUR')
# ==========================================================================
gt = read(J(ROOT, 'wellness', 'templates', 'wellness', 'greeting.html'))
rt = read(J(ROOT, 'wellness', 'templates', 'wellness', 'recipe.html'))
ok("{% url 'wellness:greeting_write' event.id %}" in gt and
   "{% url 'wellness:recipe_cooked' recipe.recipe_id %}" in rt and
   "'celebration_greeting'" not in gt and "{% url 'recipe_cooked'" not in rt,
   'SOURCE: both ask under /wellness/, nothing under the main app')
ok('ctl.abort()' in gt and "text.placeholder = 'Write your message here'" in gt,
   '  the greeting gives up after a while, and leaves the box ready')
if have_db:
    import time as _t
    import importlib
    from wellness import session as WS
    from wellness.models import WellnessProfile
    from pages.models import (HouseholdMember, Contact, CelebrationEvent,
                              RecipeCook, UserProfile)
    from pages.workspace import ensure_workspace
    from django.utils import timezone
    CG = importlib.import_module('pages.views.celebration_gifts')
    PHONE = ('Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 '
             '(KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36')
    try:
        with transaction.atomic():
            u = User.objects.create_user('p5_a', 'p5a@example.com', 'x')
            for code in ('can_access_wellness', 'can_access_celebrations',
                         'can_access_recipes'):
                pm, _ = Permission.objects.get_or_create(
                    codename=code, content_type__app_label='auth',
                    defaults={'name': code})
                u.user_permissions.add(pm)
            WellnessProfile.objects.create(user=u, onboarded=True)
            ws = ensure_workspace(u)
            c = Client(SERVER_NAME='localhost', HTTP_USER_AGENT=PHONE)
            c.force_login(u)
            UserProfile.objects.update_or_create(user=u,
                                                 defaults={'workspace': ws})
            m = HouseholdMember.objects.create(workspace=ws, name='P5',
                                               user=u)
            k = Contact.objects.create(name='P5 Eleni', relationship='friend',
                                       workspace=ws, created_by=u)
            day = timezone.localdate()
            e = CelebrationEvent.objects.create(
                contact=k, event_type='birthday', created_by=u,
                event_date=day.replace(year=day.year - 30))
            e.relevant_to.add(m)
            r0 = Recipe.objects.create(recipe_name='P5 soup', servings=2)
            c.get('/wellness/')                       # marks the session long
            sess = c.session
            sess[WS.MAIN_UNTIL] = int(_t.time()) - 60  # the hour has run out
            sess.save()
            r = c.post('/celebrations/event/%d/greeting/' % e.pk,
                       {'language': 'English'})
            ok(r.status_code == 302 and '/login/' in r['Location'],
               'CONTROL: the old address now meets the login page - what the '
               'phone saw')
            real = CG.ask_greeting
            CG.ask_greeting = lambda prompt, client=None: 'Happy birthday!'
            try:
                r = c.post('/wellness/greeting/%d/write/' % e.pk,
                           {'language': 'English'})
                ok(r.status_code == 200 and
                   r.json().get('text') == 'Happy birthday!',
                   'GREETING through Wellness: written, on the same phone')
            finally:
                CG.ask_greeting = real
            r = c.post('/wellness/recipe/%d/cooked/' % r0.pk,
                       {'rating': '4', 'from': 'wellness',
                        'cooked_on': day.isoformat()})
            ok(r.status_code == 302 and
               r['Location'].startswith('/wellness/recipe/%d/' % r0.pk) and
               RecipeCook.objects.filter(user=u, recipe=r0,
                                         rating=4).exists(),
               'COOKED IT through Wellness: saved, and back in Wellness')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL')
# ==========================================================================
try:
    ok('render_list' not in was(J(PT, 'recipe_management.html')),
       'before this round: the list was built on every visit')
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
