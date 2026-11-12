# -*- coding: utf-8 -*-
"""test_meal_share.py - round MS-1, 12 Nov 2026.

RELEASE 69 - ONE MEAL PLAN PER PERSON, SHARED WITH WHOM THEY CHOOSE.
Demetri, 14:38-14:44: "just one meal plan per person ... They can select
who to share the meal plan with ... they must be able to view their own
meal plan, or the one that they have been added to. They must also be
able to edit the meal plan that they have been added to."
14:44: "Put them into my meal plan and share it only with Angy for right
now." - by a backfill command, dry by default.
15:20: "if I'm on my phone, the phone camera should allow me to take a
photo." - Take a photo / Choose from gallery on Add a photo.
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

SUFFIX = '.bak_mealshare'
ME = 'test_meal_share.py'
PATCHER = 'apply_meal_share.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
VIEWS = J(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')

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
v = read(VIEWS)
ok(not re.search(r'MealEntry\.objects(?!\.create\(calendar=MC\.current\(\), )', v),
   'EVERY MEAL the planner reads goes through the plan being looked at; '
   'every meal it writes is put on it')
ok(v.count('MC.entries()') >= 20,
   '  (%d reads through MC.entries())' % v.count('MC.entries()'))
mc = read(J(ROOT, 'pages', 'meal_calendar.py'))
ok("Q(calendar=cal) | Q(calendar__isnull=True)" in mc and
   '_CURRENT.reset(token)' in mc,
   '  meals from before sharing show in every plan until the backfill; '
   'the plan is set for one request only')
st = read(J(ROOT, 'mysite', 'settings.py'))
ok('"pages.meal_calendar.MealCalendarMiddleware",' in st and
   st.index('AuthenticationMiddleware') < st.index('MealCalendarMiddleware'),
   '  worked out after sign-in, for every meal_plans/ address')
bf = read(J(ROOT, 'pages', 'management', 'commands',
            'meal_calendar_backfill.py'))
ok("if not opts['apply']:" in bf and 'DRY RUN - nothing was written' in bf,
   'THE BACKFILL is a dry run unless --apply')
pt = read(J(ROOT, 'pages', 'templates', 'meal_planner.html'))
ok('data-meal-calendar' in pt and "{% url 'meal_plan_share' %}" in pt and
   'data-meal-calendar-tab' in pt and 'id="mealShareModal"' in pt,
   'THE PLANNER says whose plan it is, offers Share (a dialog), and '
   'switches when one is shared with you')
ok('Your own plan.</strong> Everyone has one meal plan.' in read(
    J(ROOT, 'pages', 'help_content', 'administration.html')),
   '  and its Help says so')
wt = read(J(ROOT, 'wellness', 'templates', 'wellness', 'photo_new.html'))
js = read(J(ROOT, 'wellness', 'assets', 'wellness.js'))
ok('data-photo-camera' in wt and 'data-photo-gallery' in wt and
   "input.setAttribute('capture', 'environment')" in js and
   "input.removeAttribute('capture')" in js,
   'PHOTOS: Take a photo opens the camera; Choose from gallery the photos')

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
    from django.core.management import call_command
    from django.utils import timezone
    import io
    from pages.models import MealEntry, MealCalendar, Recipe
    connection.ensure_connection()
    MealCalendar.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    if '*' not in _dj.ALLOWED_HOSTS and 'localhost' not in _dj.ALLOWED_HOSTS:
        _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['localhost']

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            perms = list(Permission.objects.filter(
                codename__in=['can_access_recipes', 'can_edit_recipes'],
                content_type__app_label='auth'))
            if len(perms) < 2:
                for code in ('can_access_recipes', 'can_edit_recipes'):
                    p, _ = Permission.objects.get_or_create(
                        codename=code, content_type__app_label='auth',
                        defaults={'name': code})
                perms = list(Permission.objects.filter(
                    codename__in=['can_access_recipes', 'can_edit_recipes'],
                    content_type__app_label='auth'))
            d = User.objects.create_user('ms1_dem', 'd@example.com', 'x',
                                         first_name='Dem')
            g = User.objects.create_user('ms1_ang', 'g@example.com', 'x',
                                         first_name='Ang')
            k = User.objects.create_user('ms1_kid', 'k@example.com', 'x',
                                         first_name='Kid')
            for u in (d, g, k):
                u.user_permissions.add(*perms)
            cd, cg, ck = (Client(SERVER_NAME='localhost') for _ in range(3))
            cd.force_login(d)
            cg.force_login(g)
            ck.force_login(k)
            # Only this suite's meals count from here on.
            MealEntry.objects.update(calendar=None)
            old_ids = list(MealEntry.objects.values_list('meal_entry_id',
                                                         flat=True))
            MealEntry.objects.all().delete()
            day = timezone.localdate()
            old = MealEntry.objects.create(date=day, note='Before sharing')

            t = cd.get('/meal_plans/?view=day&date=%s' % day).content.decode()
            ok("Dem&#x27;s meal plan" in t and 'Before sharing' in t and
               'data-meal-calendar-tab' not in t and
               'id="mealShareModal"' in t,
               'A PLAN EACH: Dem sees "Dem\'s meal plan", the meal from '
               'before sharing, and no switcher')
            ok('Before sharing' in ck.get('/meal_plans/?view=day&date=%s'
                                          % day).content.decode(),
               '  until the backfill, everybody still sees the old meals')
            cd.post('/meal_plans/note/', {'date': day.isoformat(),
                                          'note': 'Dem cooks'})
            cg.post('/meal_plans/note/', {'date': day.isoformat(),
                                          'note': 'Ang cooks'})
            dn = MealEntry.objects.get(note='Dem cooks')
            ok(dn.calendar and dn.calendar.owner_id == d.pk,
               'A NEW MEAL goes on the plan of whoever added it')
            td = cd.get('/meal_plans/?view=day&date=%s' % day).content.decode()
            tg = cg.get('/meal_plans/?view=day&date=%s' % day).content.decode()
            ok('Dem cooks' in td and 'Ang cooks' not in td and
               'Ang cooks' in tg and 'Dem cooks' not in tg,
               '  and nobody sees anyone else\'s plan')
            r = cg.post('/meal_plans/remove/', {
                'meal_entry_id': dn.meal_entry_id, 'entry_id':
                dn.meal_entry_id})
            ok(MealEntry.objects.filter(pk=dn.pk).exists(),
               '  nor can they remove a meal from it')
            # ---- sharing
            r = cd.post('/meal_plans/share/', {'share': [str(g.pk)]})
            cal = MealCalendar.objects.get(owner=d)
            ok(r.status_code == 302 and
               list(cal.shared_with.values_list('pk', flat=True)) == [g.pk],
               'SHARE: Dem ticks Ang')
            tg = cg.get('/meal_plans/?view=day&date=%s' % day).content.decode()
            ok(tg.count('data-meal-calendar-tab') == 2 and
               "Dem&#x27;s meal plan" in tg and
               'My meal plan' in tg,
               '  Ang now has a switcher: My meal plan, Dem\'s meal plan')
            tg = cg.get('/meal_plans/?view=day&date=%s&calendar=%d'
                        % (day, cal.pk)).content.decode()
            ok('Dem cooks' in tg and 'Ang cooks' not in tg and
               'Shared with you' in tg,
               '  and switching shows Dem\'s meals, saying it is shared')
            cg.post('/meal_plans/note/', {'date': day.isoformat(),
                                          'note': 'Ang adds to Dem'})
            ok(MealEntry.objects.get(note='Ang adds to Dem').calendar_id ==
               cal.pk,
               '  what Ang adds there lands on Dem\'s plan (remembered '
               'between pages)')
            ok('Ang adds to Dem' in cd.get('/meal_plans/?view=day&date=%s'
                                           % day).content.decode(),
               '  and Dem sees it')
            tk = ck.get('/meal_plans/?view=day&date=%s&calendar=%d'
                        % (day, cal.pk)).content.decode()
            ok('Dem cooks' not in tk,
               '  Kid, not shared with, asking for Dem\'s plan gets his own')
            ok('id="mealShareModal"' not in tg and
               'Share Ang&#x27;s meal plan' in cg.get(
                   '/meal_plans/?view=day&date=%s&calendar=%d' % (
                       day, MealCalendar.objects.get(owner=g).pk))
               .content.decode(),
               '  Share is only offered on your own plan')
            cd.post('/meal_plans/share/', {})
            tg = cg.get('/meal_plans/?view=day&date=%s&calendar=%d'
                        % (day, cal.pk)).content.decode()
            ok('Dem cooks' not in tg and 'data-meal-calendar-tab' not in tg,
               'UNSHARE: Ang loses Dem\'s plan and the switcher')
            # ---- the backfill
            out = io.StringIO()
            call_command('meal_calendar_backfill', stdout=out)
            ok('Meals with no plan yet: 1' in out.getvalue() and
               'ms1_ang (Ang)' in out.getvalue(),
               'BACKFILL with no names lists the meals and the people')
            out = io.StringIO()
            call_command('meal_calendar_backfill', owner='ms1_dem',
                         share='ms1_ang', stdout=out)
            old.refresh_from_db()
            ok('DRY RUN' in out.getvalue() and old.calendar_id is None,
               '  with names, a dry run: says what it would do, writes '
               'nothing')
            out = io.StringIO()
            call_command('meal_calendar_backfill', owner='ms1_dem',
                         share='ms1_ang', apply=True, stdout=out)
            old.refresh_from_db()
            ok(old.calendar_id == cal.pk and
               list(cal.shared_with.values_list('pk', flat=True)) == [g.pk],
               '  --apply: the old meal is on Dem\'s plan, shared with Ang')
            ok('Before sharing' not in ck.get(
                '/meal_plans/?view=day&date=%s' % day).content.decode(),
               '  and Kid no longer sees it')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL')
# ==========================================================================
try:
    ok('MC.entries()' not in read(VIEWS + SUFFIX) and
       'class MealCalendar' not in read(J(ROOT, 'pages', 'models.py') +
                                        SUFFIX),
       'before this round: one calendar for everybody')
except IOError as _e:
    skip('section 3', str(_e))

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'class MealCalendarMiddleware:'" in gate,
   '  with a sentinel on the plan chooser')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
