# -*- coding: utf-8 -*-
"""test_doc_recipe.py - rounds DC-1 and RC-3, 12 Nov 2026.

RELEASES 71 AND 72, ONE BUNDLE (Demetri, 18:25: "Can we not bundle 71
and 72?").
  71 DOCUMENTS - "We can add these additional document types. We can add
     earlier reminder for slow renewals as an optional choice."
  72 RECIPES - "All Recipe improvements sound good": Cooked it with a
     rating and a note, cook mode; and the recipe page stops fetching every
     ingredient for nothing. (Reordering the meals on a day was already
     there - RO-1, 21 Oct.)
Also: meal_calendar_backfill names its database first, like every other
tool that can run against Live.
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

SUFFIX = '.bak_docrecipe'
ME = 'test_doc_recipe.py'
PATCHER = 'apply_doc_recipe.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
P = J(ROOT, 'pages')
T = J(P, 'templates')

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
m = read(J(P, 'models.py'))
ok(all(("('%s', '%s')" % kv) in m for kv in (
    ('health', 'Health Card'), ('residence', 'Residence Certificate'),
    ('car_reg', 'Car Registration'), ('mot', 'MOT'),
    ('insurance', 'Insurance'), ('tax_id', 'Tax ID'))),
   'DOCUMENTS: six more types')
ok("REMIND_CHOICES = [(9, '9 months before'), (12, '12 months before')]"
   in m and "REMIND_DAYS = {None: 180, 9: 270, 12: 365}" in m,
   '  and Remind me: the usual six months, or 9 or 12')
ck = read(J(P, 'management', 'commands',
            'check_lease_renewal_and_invoices.py'))
ok('Passport.REMIND_DAYS.get(passport.remind_months' in ck,
   '  the 1st-and-15th email honours each document\'s own window')
pm = read(J(T, 'passport_management.html'))
ok('name="remind_months"' in pm and 'data-remind-for="{{ passport.id }}"'
   in pm, '  the form asks, and Edit reads it back from the row')
vr = read(J(T, 'view_recipe.html'))
ok('data-cook-open' in vr and 'data-cook-screen' in vr and
   "navigator.wakeLock.request('screen')" in vr and
   'data-minutes="{{ instruction.time_estimate' in vr,
   'COOK MODE: one step at a time, screen on, a timer from the step\'s '
   'minutes')
ok("{% url 'recipe_cooked' recipe.recipe_id %}" in vr and
   'data-cooked-summary' in vr and 'name="rating"' in vr,
   'COOKED IT: stars, a note, and "last cooked ..."')
rc = read(J(P, 'views', 'recipes', 'recipe_crud.py'))
ok("'ingredient_categories'" not in rc.split("RC-3, 12 Nov 2026 - 'ingr")[0]
   .split('def recipe_management')[-1] and
   "IngredientCategory.objects.prefetch_related('ingredient_set')" not in rc,
   'RECIPE MANAGEMENT no longer fetches every ingredient for nothing')
bf = read(J(P, 'management', 'commands', 'meal_calendar_backfill.py'))
ok('print_banner(self.stdout.write)' in bf,
   'THE BACKFILL names its database before anything else')
hc = read(J(P, 'help_content', 'administration.html'))
ok('Cook mode</div>' in hc and 'Cooked it</div>' in hc and
   'Set Remind me to 9 or 12 months.' in hc,
   'HELP: cook mode, Cooked it and Remind me')

# ==========================================================================
head('2. DRIVEN')
# ==========================================================================
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
import datetime as dt                                       # noqa: E402
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User, Permission
    from django.utils import timezone
    from pages.models import Recipe, RecipeCook, Passport
    connection.ensure_connection()
    RecipeCook.objects.exists()
    Passport.objects.filter(remind_months=9).exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2', 'no database, or migrate not run yet: %s'
         % str(_e).split('\n')[0][:70])

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            def perm(code):
                p, _ = Permission.objects.get_or_create(
                    codename=code, content_type__app_label='auth',
                    defaults={'name': code})
                return p
            a = User.objects.create_user('dr_a', 'a@example.com', 'x')
            b = User.objects.create_user('dr_b', 'b@example.com', 'x')
            for u in (a, b):
                u.user_permissions.add(perm('can_access_recipes'))
            ca, cb = Client(SERVER_NAME='localhost'), \
                Client(SERVER_NAME='localhost')
            ca.force_login(a)
            cb.force_login(b)
            r = Recipe.objects.create(recipe_name='DR soup', servings=4)
            day = timezone.localdate()
            res = ca.post('/recipe/%d/cooked/' % r.recipe_id,
                          {'rating': '4', 'note': 'DR too salty',
                           'cooked_on': (day - dt.timedelta(days=21))
                           .isoformat()})
            ca.post('/recipe/%d/cooked/' % r.recipe_id,
                    {'rating': '5', 'cooked_on': day.isoformat()})
            mine = list(RecipeCook.objects.filter(user=a, recipe=r))
            ok(res.status_code == 302 and len(mine) == 2 and
               mine[-1].note == 'DR too salty',
               'COOKED IT: two cooks saved, with ratings and a note')
            t = ca.get('/view_recipe/%d/' % r.recipe_id).content.decode()
            ok('Last cooked today' in t and '2 times' in t and
               '4.5&#9733; on average' in t,
               '  the recipe says: last cooked today, 2 times, 4.5 on average')
            tb = cb.get('/view_recipe/%d/' % r.recipe_id).content.decode()
            ok('Not cooked yet' in tb and 'DR too salty' not in tb,
               '  and nobody else sees them', tb[:300] if 'Not cooked' not in
               tb else [l for l in tb.splitlines() if 'salty' in l][:2])
            cb.post('/recipe/%d/cooked/' % r.recipe_id,
                    {'delete': str(mine[0].pk)})
            ok(RecipeCook.objects.filter(pk=mine[0].pk).exists(),
               '  nor can they remove one')
            ca.post('/recipe/%d/cooked/' % r.recipe_id,
                    {'rating': '3', 'cooked_on': (day + dt.timedelta(
                        days=5)).isoformat()})
            ok(RecipeCook.objects.filter(user=a).order_by('-created_at')
               .first().cooked_on == day,
               '  a date in the future is read as today')
            # ---- the expiry email window
            from pages.management.commands import \
                check_lease_renewal_and_invoices as CK
            from pages.workspace import ensure_workspace
            ws = ensure_workspace(a)
            mk = lambda n, days, rm: Passport.objects.create(   # noqa: E731
                workspace=ws, holder_name=n, document_type='passport',
                document_number=n, country_of_issue='Greece', status='active',
                expiry_date=day + dt.timedelta(days=days), remind_months=rm)
            mk('DR_six', 150, None)
            mk('DR_far', 250, None)
            mk('DR_nine', 250, 9)
            mk('DR_twelve', 350, 12)
            mk('DR_toofar', 400, 12)
            cmd = CK.Command()
            got = {p['holder_name'] for p in cmd.get_expiring_passports()
                   if p['holder_name'].startswith('DR_')}
            ok(got == {'DR_six', 'DR_nine', 'DR_twelve'},
               'REMIND ME: six months as usual; 9 and 12 when asked; never '
               'beyond', sorted(got))
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. CONTROL')
# ==========================================================================
try:
    ok("('mot', 'MOT')" not in was(J(P, 'models.py')) and
       'data-cook-open' not in was(J(T, 'view_recipe.html')),
       'before this round: no MOT, no cook mode')
except IOError as _e:
    skip('section 3', str(_e))

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402
ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'class RecipeCook(models.Model):'" in gate,
   '  with a sentinel on Cooked it')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
