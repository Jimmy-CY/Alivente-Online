# -*- coding: utf-8 -*-
"""test_wellness_twentyfive.py - round PT-2, 12 Nov 2026.

RELEASE 73 - AT HOME TODAY IS ONE CARD; A RECIPE OPENS INSIDE WELLNESS.
Demetri, 21:40-21:48, having used PT-1: celebrations "only today (non-
clickable and non-expandable)"; every recipe planned today, opening "without
exiting to the recipe module", with Cook mode; his expiring documents, not
clickable - and he expected to see two passports and saw none. The page
behind See all goes ("Yes", 21:48).
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

SUFFIX = '.bak_todaycard'
ME = 'test_wellness_twentyfive.py'
PATCHER = 'apply_today_card.py'
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

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
hm = read(J(APP, 'home.py'))
ok('def card(user, day):' in hm and 'def card_lines' not in hm and
   'e.get_next_occurrence() != day' in hm,
   'HOME: one card; celebrations are today\'s only')
ok("Passport.REMIND_DAYS.get(p.remind_months, 180)" in hm and
   "status__in=('active', 'renewal')" in hm and 'PH.matches(' in hm,
   '  documents from their own reminder window, by link or by name')
td = read(J(WT, 'today.html'))
ok("{% url 'wellness:recipe' m.recipe_id %}" in td and
   "wellness:home" not in td and 'See all' not in td,
   'TODAY: a recipe line opens the recipe in Wellness; no See all')
cel = td[td.index('{% for r in home.cel %}'):td.index('{% endfor %}',
                                                      td.index('{% for r in home.cel %}'))]
doc = td[td.index('{% for d in home.docs %}'):td.index('{% endfor %}',
                                                       td.index('{% for d in home.docs %}'))]
# PT-4, 13 Nov 2026 - a celebration now opens its greeting (Demetri, 09:01);
# documents stay plain lines. test_wellness_twentysix holds the greeting.
ok('<a ' not in doc,
   '  documents are plain lines, not links')
ok(not os.path.isfile(J(WT, 'home.html')),
   'THE PAGE: wellness/home.html is gone',
   'delete wellness\\templates\\wellness\\home.html before pushing')
urls = read(J(APP, 'urls.py'))
ok("name='home'" not in urls and "name='recipe'" in urls,
   '  its address too; the recipe has one')
# Cook mode is ONE screen and ONE script, in two places. Hold them together.
def cook(t):
    i = t.index('<div class="cm-screen" data-cook-screen')
    return t[i:t.index('</script>', i)]
vr = read(J(ROOT, 'pages', 'templates', 'view_recipe.html'))
rc = read(J(WT, 'recipe.html'))
ok(cook(vr) == cook(rc), 'COOK MODE: the Wellness copy is the Recipes one, '
   'character for character')
ok('name="from" value="wellness"' in rc and
   "request.POST.get('from') == 'wellness'" in
   read(J(ROOT, 'pages', 'views', 'recipes', 'recipe_extras.py')),
   '  and Cooked it comes back to the Wellness page')
pv = read(J(ROOT, 'pages', 'views', 'passports.py'))
ok('holder=PH.member_for(workspace.pk, holder_name)' in pv and
   'PH.member_for(passport.workspace_id, passport.holder_name)' in pv,
   'DOCUMENTS: adding or editing one links it to its holder')
css = read(J(APP, 'assets', 'wellness.css'))
mins = re.findall(r'min-height:\s*(\d+)px', css)
ok(all(int(m) >= 44 for m in mins), '  still no min-height under 44px')
base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
v = read(J(APP, 'views.py'))
ok(vv and len(set(vv)) == 1 and vv[0] not in ('wl22-1', 'wl23-1') and
   ("SW_VERSION = '%s'" % vv[0]) in v, 'the app files carry a new version',
   vv)

# ==========================================================================
head('2. THE RULE FOR NAMES')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
class M(object):
    def __init__(self, pk, name):
        self.pk, self.name = pk, name
from pages.management.commands.backfill_passport_holder import ALIASES  # noqa
from pages import passport_holder as PH                     # noqa: E402
fam = [M(1, 'Demetri'), M(2, 'Erene'), M(3, 'Angy')]
ok([m.pk for m in PH.matches(fam, 'Demetri')] == [1] and
   [m.pk for m in PH.matches(fam, ' demetri ')] == [1],
   'exact, and loose once case and spacing are folded')
ok([m.pk for m in PH.matches(fam, 'Demetri Manias')] == [1] and
   [m.pk for m in PH.matches(fam, 'ANGELA  manias')] == [3],
   '  named: the October list - "Demetri Manias" is Demetri')
ok(PH.matches(fam, 'Stella') == [] and
   len(PH.matches(fam + [M(4, 'demetri')], 'Demetri ')) == 2,
   '  nobody is nobody; two who match are two, and member_for takes '
   'neither')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
import datetime as dt                                       # noqa: E402
from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
ok(HELP.for_url_name('recipe') and not HELP.SCREENS.get('home') and
   'Cook mode' in ' '.join(HELP.for_url_name('today')['steps']),
   'HELP: the recipe screen; Today says what the card holds')
ok(all(len(s.split()) <= 40 for s in HELP.for_url_name('recipe')['steps'] +
       HELP.for_url_name('today')['steps']), '  every step 40 words or fewer')
qs = {h['q']: h for h in G.HOWTO}
ok('Cook mode' in qs.get('What is At home today?', {}).get('a', '') and
   'See all' not in qs.get('What is At home today?', {}).get('a', ''),
   '  and the guide answer no longer mentions See all')
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from wellness.models import WellnessProfile
    from pages.models import (HouseholdMember, Contact, CelebrationEvent,
                              Passport, MealEntry, MealCalendar, Recipe,
                              RecipeInstruction, RecipeCook)
    connection.ensure_connection()
    RecipeCook.objects.exists()
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
            a = User.objects.create_user('w25_a', 'w25a@example.com', 'x',
                                         first_name='Al')
            b = User.objects.create_user('w25_b', 'w25b@example.com', 'x',
                                         first_name='Bo')
            for u in (a, b):
                u.user_permissions.add(perm('can_access_wellness'))
                WellnessProfile.objects.create(user=u, onboarded=True)
            a.user_permissions.add(perm('can_access_celebrations'),
                                   perm('can_access_recipes'),
                                   perm('can_access_passports'),
                                   perm('can_edit_passports'))
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            day = timezone.localdate()
            ws = ensure_workspace(a)
            ma = HouseholdMember.objects.create(workspace=ws, name='W25 Al',
                                                user=a)
            mb = HouseholdMember.objects.create(workspace=ws, name='W25 Bo',
                                                user=b)

            def contact(n):
                return Contact.objects.create(name=n, relationship='other',
                                              workspace=ws, created_by=a)

            def event(c, when, who, kind='birthday'):
                e = CelebrationEvent.objects.create(
                    contact=c, event_type=kind, created_by=a,
                    event_date=when)
                e.relevant_to.add(who)
                return e
            event(contact('Kiddo'), day.replace(year=day.year - 21), ma)
            event(contact('W25 Later'), (day + dt.timedelta(days=3))
                  .replace(year=1990), ma)
            event(contact('W25 Nobody'), day.replace(year=1980), mb)

            def doc(name, holder, kind, country, days, **kw):
                return Passport.objects.create(
                    workspace=ws, holder_name=name, holder=holder,
                    document_type=kind, document_number='W25',
                    country_of_issue=country,
                    expiry_date=day + dt.timedelta(days=days), **kw)
            doc('W25 Al', ma, 'passport', 'Greece', 105, status='active')
            doc('w25  al', None, 'passport', 'South Africa', -331,
                status='active')
            doc('W25 Al', None, 'drivers_license', 'Cyprus', 250,
                status='active')
            doc('W25 Al', None, 'id', 'Spain', 250, status='active',
                remind_months=9)
            doc('W25 Al', None, 'mot', 'Cyprus', 20, status='renewal')
            doc('W25 Al', ma, 'visa', 'Ireland', 10, status='inactive')
            doc('W25 Bo', mb, 'passport', 'Italy', 10, status='active')

            r = Recipe.objects.create(recipe_name='W25 lentil soup',
                                      servings=4)
            RecipeInstruction.objects.create(recipe=r, step_number=1,
                                             instruction_text='W25 chop')
            RecipeInstruction.objects.create(recipe=r, step_number=2,
                                             instruction_text='W25 simmer',
                                             time_estimate=20)
            cal = MealCalendar.objects.create(owner=a)
            MealEntry.objects.create(date=day, recipe=r, calendar=cal)
            MealEntry.objects.create(date=day, note='W25 eat out',
                                     calendar=cal)
            MealEntry.objects.create(date=day + dt.timedelta(days=1),
                                     note='W25 tomorrow', calendar=cal)

            t = ca.get('/wellness/').content.decode()
            ok('data-home-card' in t and 'Kiddo' in t and
               'Birthday, turns 21' in t,
               'CARD: Kiddo turns 21 today')
            ok('W25 Later' not in t and 'W25 Nobody' not in t,
               '  not one in three days, and not Bo\'s')
            ok(t.count('data-home-meal') == 2 and
               ('/wellness/recipe/%d/' % r.pk) in t and 'W25 eat out' in t
               and 'W25 tomorrow' not in t,
               '  every meal today: the recipe links into Wellness, the '
               'note is a line')
            ok('Greek passport' in t and 'In 105 days' in t,
               '  his Greek passport, 105 days away - six months is the '
               'window, not 90 days')
            ok('South African passport' in t and 'Expired' in t,
               '  the expired one still marked Active, by its typed name '
               'and no link')
            ok('Spanish ID' in t and 'Cyprus driver' not in t,
               '  250 days: shown when Remind me is 9 months, not when it '
               'is the usual 6')
            ok('Cyprus MOT' in t and 'renewal applied for' in t,
               '  one applied for says so')
            ok('Irish visa' not in t and 'Italian passport' not in t,
               '  not an inactive one, and not Bo\'s')
            ok('data-home-card' not in cb.get('/wellness/').content.decode(),
               'Bo, who cannot open those parts of Alivente, gets no card')
            ok(ca.get('/wellness/home/').status_code == 404,
               'THE PAGE behind See all is gone')

            t = ca.get('/wellness/recipe/%d/' % r.pk).content.decode()
            ok('W25 lentil soup' in t and 'W25 simmer' in t and
               'data-cook-open' in t and 'data-cook-screen' in t and
               'data-minutes="20"' in t,
               'RECIPE: in Wellness, with its method and Cook mode')
            ok("{% url 'personal_page' %}" not in rc and
               "wellness:today" in rc, '  "Today" goes back; nothing leaves '
               'Wellness')
            ok(cb.get('/wellness/recipe/%d/' % r.pk).status_code == 403,
               '  someone who cannot open Recipes cannot open it here')
            rr = ca.post('/recipe/%d/cooked/' % r.pk,
                         {'rating': '5', 'note': 'W25 lovely',
                          'cooked_on': day.isoformat(),
                          'from': 'wellness'})
            ok(rr.status_code == 302 and rr['Location'].startswith(
                '/wellness/recipe/%d/' % r.pk) and
               RecipeCook.objects.filter(user=a, recipe=r,
                                         rating=5).exists(),
               'COOKED IT from Wellness is saved, and lands back in '
               'Wellness')
            rr = ca.post('/recipe/%d/cooked/' % r.pk,
                         {'rating': '4', 'from': 'https://example.com/'})
            ok(rr.status_code == 302 and rr['Location'].startswith(
                '/view_recipe/%d/' % r.pk),
               '  anything else posted as "from" goes to Recipes, never '
               'elsewhere')
            t = ca.get('/wellness/recipe/%d/' % r.pk).content.decode()
            ok('W25 lovely' in t and '5&#9733;' in t,
               '  and the page shows it')

            # A new document is linked to its holder from the start.
            ca.post('/passport-management/', {
                'action': 'add', 'holder_name': 'W25 Al',
                'document_type': 'health', 'document_number': 'W25H',
                'country_of_issue': 'Cyprus', 'status': 'active',
                'expiry_date': (day + dt.timedelta(days=30)).isoformat()})
            p = Passport.objects.filter(document_number='W25H').first()
            ok(p is not None and p.holder_id == ma.pk,
               'DOCUMENTS: one added for "W25 Al" is linked to him')
            ca.post('/passport-management/', {
                'action': 'edit', 'passport_id': p.pk,
                'holder_name': 'Somebody Else', 'document_type': 'health',
                'document_number': 'W25H', 'country_of_issue': 'Cyprus',
                'status': 'active'})
            p.refresh_from_db()
            ok(p.holder_id is None,
               '  renamed to nobody in the household, the link goes - it '
               'no longer says who it was')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. CONTROL')
# ==========================================================================
try:
    ok('def card_lines(g):' in was(J(APP, 'home.py')) and
       "path('home/'" in was(J(APP, 'urls.py')),
       'before this round: the card was three lines and See all had a page')
except IOError as _e:
    skip('section 4', str(_e))

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def recipe(request, recipe_id):'" in gate and
   "Text = 'def member_for(workspace_id, holder_name):'" in gate,
   '  with sentinels on the recipe page and the name rule')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
