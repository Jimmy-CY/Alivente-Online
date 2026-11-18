# -*- coding: utf-8 -*-
"""test_recipe_units_null.py - round RU-1, 18 Nov 2026.

RELEASE 99 - RECIPES: ADDING A MEASUREMENT WORKS AGAIN.
Demetri, 18 Nov: "I can't seem to add a measurement in recipes" - the box
said Error: 'NoneType' object has no attribute 'strip'. Two faults. With
Abbreviation left blank the view saved None, and since migration 0095
(N1) the column is NOT NULL, so MySQL refused the row. Then the failed
try cleared the remembered name while the box stayed open, so Add sent
no name and the server called .strip() on None. Now the name is read from
the box, kept until it succeeds, and the server reads every field
null-safe. The same for the Add ingredient box. And the phone Travel help
says the app fetches its new look by itself.
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

SUFFIX = '.bak_units1'
ME = 'test_recipe_units_null.py'
PATCHER = 'apply_recipe_units_null.py'
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
import json                                                 # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
UV = J(ROOT, 'pages', 'views', 'recipes', 'units.py')
TP = J(ROOT, 'pages', 'templates', 'preview_imported_recipe.html')

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
uv = read(UV)
ok(".get('name', '').strip()" not in uv and
   ".get('abbreviation', '').strip()" not in uv,
   "units.py: no field read as data.get(key, '').strip() any more")
ok("def text(key):" in uv and "str(data.get(key) or '').strip()" in uv,
   '  add_measurement_ajax reads every field null-safe')
ok('else None' not in uv,
   "BLANK IS '': no optional field is written as None - since migration "
   "0095 the columns are NOT NULL, and MySQL refused the row")
tp = read(TP)
cm = tp[tp.index('function confirmAddMeasurement()'):
        tp.index('// ==================== INGREDIENT DROPDOWN')]
ok("getElementById('newMeasurementName').value" in cm,
   'THE BOX: the name is read from the box itself')
ok('.finally(' in cm and 'pendingMeasurementName = null'
   not in cm.split('.finally(')[1],
   '  and is no longer forgotten when a try fails')
ci = tp[tp.index('function confirmAddIngredient()'):]
ci = ci[:ci.index('\n}\n')]
ok("getElementById('newIngredientName').value" in ci and
   'pendingIngredientName = null' not in ci.split('.finally(')[1],
   '  the Add ingredient box the same')
ok('fetches its new look by itself' in read(J(ROOT, 'travel', 'templates',
                                              'travel', 'm', 'help.html')),
   'PHONE TRAVEL HELP: the app fetches its new look by itself')
try:
    ok("name = data.get('name', '').strip()" in was(UV),
       "CONTROL: before this round the name was read with .get(key, '')")
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
    from pages.models import MeasurementUnit
    connection.ensure_connection()
    MeasurementUnit.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 2 (database)', str(_e).split('\n')[0][:70])

if have_db:
    from django.conf import settings as _dj
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    from django.urls import reverse

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            u = User.objects.create_user('ru1a', 'ru1a@example.com', 'x')
            for code in ('can_access_recipes', 'can_edit_recipes'):
                perm, _ = Permission.objects.get_or_create(
                    codename=code, content_type__app_label='auth',
                    defaults={'name': code})
                u.user_permissions.add(perm)
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)
            url = reverse('add_measurement_ajax')

            def post(d):
                r = c.post(url, json.dumps(d),
                           content_type='application/json')
                return r.json()
            out = post({'name': None, 'name_plural': None,
                        'abbreviation': None, 'abbreviation_plural': None,
                        'unit_type': None})
            ok(out['success'] is False and 'strip' not in out['message']
               and 'no name' in out['message'],
               'NO NAME: a plain sentence, never a Python error', out)
            out = post({'name': 'ru1 handful', 'name_plural': None,
                        'abbreviation': None, 'abbreviation_plural': '',
                        'unit_type': 'count'})
            mu = MeasurementUnit.objects.filter(name='ru1 handful').first()
            ok(out['success'] is True and mu and mu.unit_type == 'count'
               and mu.abbreviation == '' and mu.name_plural == '',
               'A MEASUREMENT with its optional fields blank is added - '
               "stored as ''", out)
            out = post({'name': 'ru1 pinchful', 'unit_type': 'nonsense'})
            ok(out['success'] is True and MeasurementUnit.objects.get(
                name='ru1 pinchful').unit_type == 'other',
               '  an unknown unit type becomes Other')
            out = post({'name': 'RU1 HANDFUL', 'unit_type': 'count'})
            ok(out['success'] is False and 'already exists' in
               out['message'], '  the same name twice is still refused')
            r = c.post(reverse('add_measurement_unit'), json.dumps(
                {'name': 'ru1 sprig', 'name_plural': '', 'abbreviation': '',
                 'abbreviation_plural': None, 'unit_type': 'count'}),
                content_type='application/json')
            mu = MeasurementUnit.objects.filter(name='ru1 sprig').first()
            ok(r.json().get('success') is True and mu and
               mu.abbreviation == '',
               'MEASUREMENT UNITS PAGE: Add with blanks works too', r.json())
            r = c.post(reverse('update_measurement_unit'), json.dumps(
                {'unit_id': mu.measurement_unit_id, 'name': 'ru1 sprig',
                 'name_plural': 'ru1 sprigs', 'abbreviation': '',
                 'abbreviation_plural': None, 'unit_type': 'count'}),
                content_type='application/json')
            mu.refresh_from_db()
            ok(r.json().get('success') is True and
               mu.name_plural == 'ru1 sprigs' and mu.abbreviation == '',
               '  and so does Edit', r.json())
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('3. REGISTERED')
# ==========================================================================
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
