# -*- coding: utf-8 -*-
"""test_ra17_send_standard_month.py - round RA17, 23 Nov 2026.

RELEASE RA17 - SEND IN THE HOUSE SHAPE, AND THE MONTH ON SCREEN.
Demetri, 23 Nov: "I think we need to standardise the look of the modal (to
our standards). Then, when I have a specific month open, or a specific
week, or a specific day, it must always send those recipes. Don't think it
works for month?" - It did not after the arrows: goMonth sent ?year= and
?month= and kept the old week, so the grid showed December while Send,
Print and the Shopping List read November. And his November reached
WhatsApp with one line of six; the ``` block was the only unusual thing.
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


import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra17'
ME = 'test_ra17_send_standard_month.py'
PATCHER = 'apply_ra17_send_standard_month.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
PG = J(ROOT, 'pages')
TPL = J(PG, 'templates', 'meal_planner.html')
VIEW = J(PG, 'views', 'recipes', 'meal_planning.py')
SEND = J(PG, 'views', 'recipes', 'meal_send.py')
GUIDE = J(PG, 'help_content', 'administration.html')

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


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])


def modal(t):
    a = t.find('id="sendModal"')
    b = t.find('<script>', a)
    return t[a:b] if 0 <= a < b else ''


def claims(t, v, s):
    m = modal(t)
    return {
        'MONTH: the arrows move the anchor to the month asked for':
            'anchor = date(year, month, 1)' in v
            and "'year' in request.GET or 'month' in request.GET" in v,
        'A MOVE FOLLOWS THE MEAL out of the period on screen':
            'def move_landing(request, when):' in v
            and v.count('return redirect(move_landing(request, when))') == 3,
        'SEND IN THE HOUSE SHAPE: a muted line saying what goes':
            'id="sendIntro"' in m and '.send-intro {' in t,
        '  bold labels over each part':
            all('<label><strong>%s</strong></label>' % x in m
                for x in ('What will be sent', 'Send by', 'Email to')),
        '  the preview a day-by-meal list, not a code box':
            'function sendDraw' in t and '<pre class="send-preview"' not in t
            and '.send-day {' in t,
        '  Cancel and the one primary in the footer':
            'data-dismiss="modal">Cancel</button>' in m
            and 'id="sendEmailBtn"' in m,
        'THE TEXT CARRIES ITS DAYS AND ITS PERIOD for the dialog':
            "'days': day_rows(by_day, start, end)" in s
            and "'period': described(view, start, end)" in s,
        '  and WhatsApp gets plain lines - no ``` block':
            "whatsapp='*' + head + '*\\n\\n' + '\\n'.join(lines)" in s,
    }


head('1. THE SOURCE')
T_NOW, V_NOW, S_NOW = read(TPL), read(VIEW), read(SEND)
for m, got in claims(T_NOW, V_NOW, S_NOW).items():
    ok(got, m)
ok(T_NOW.count('{%') == T_NOW.count('%}'), 'the planner template tags balance')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in (TPL, VIEW, SEND)):
    held = [m for m, got in claims(read(TPL + SUFFIX), read(VIEW + SUFFIX),
                                   read(SEND + SUFFIX)).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA17', held)
else:
    skip('the control', 'no .bak_ra17 beside the files')

head('3. DRIVEN (database; no network)')
import datetime as dt                                       # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']
have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import Permission, User
    from pages.models import MealEntry, Recipe
    connection.ensure_connection()
    MealEntry.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database)', str(_e).split('\n')[0][:70])

if have_db:
    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            ed = User.objects.create_user('ra17e', 'ra17e@example.com', 'pw')
            for cn in ('can_access_recipes', 'can_edit_recipes'):
                ed.user_permissions.add(Permission.objects.get(codename=cn))
            E_ = Client()
            E_.force_login(ed)

            def mk(day, name):
                r = Recipe.objects.create(recipe_name=name, servings=4,
                                          prep_time=5, cook_time=25)
                return MealEntry.objects.create(date=day, recipe=r,
                                                servings=4, created_by=ed)
            mk(dt.date(2031, 11, 24), 'November soup')
            mk(dt.date(2031, 12, 10), 'December pie')
            mk(dt.date(2031, 12, 10), 'December salad')

            # THE ARROWS: goMonth sends ?year= and ?month= and the OLD week.
            p = E_.get('/meal_plans/planner/', {
                'view': 'month', 'year': '2031', 'month': '12',
                'week': '2031-11-24'}).content.decode()
            ok('date=2031-12-01' in p,
               'AFTER › TO DECEMBER the page is about December - Send asks '
               'for 2031-12-01', re.findall(r'date=\d{4}-\d\d-\d\d', p)[:4])
            ok('from=2031-12-01&amp;to=2031-12-31' in p,
               '  and Print and the Shopping List buy and print December')
            p = E_.get('/meal_plans/planner/', {
                'view': 'month', 'date': '2031-11-24'}).content.decode()
            ok('date=2031-11-24' in p and 'from=2031-11-01&amp;to=2031-11-30'
               in p, '  while a month reached by date keeps its own day')
            p = E_.get('/meal_plans/planner/', {
                'view': 'month', 'year': '2031', 'month': '11',
                'date': '2031-11-24'}).content.decode()
            ok('date=2031-11-24' in p,
               '  and naming the month you are already in moves nothing')

            r = E_.get('/meal_plans/send/', {'view': 'month',
                                             'date': '2031-12-01'})
            d = json.loads(r.content.decode())
            ok(d.get('period') == 'December 2031' and
               [x['label'] for x in d.get('days', [])] == ['Wed (10th Dec)']
               and d['days'][0]['names'] == ['December pie',
                                             'December salad'],
               'SEND FOR DECEMBER: December\'s meals, a day to a row',
               d.get('days'))
            ok('November soup' not in d.get('text', '') and
               'November soup' not in d.get('whatsapp', ''),
               '  and nothing from November')
            ok('```' not in d.get('whatsapp', '') and
               d['whatsapp'].endswith('Wed (10th Dec): December pie\n'
                                      '                December salad'),
               '  WhatsApp: plain lines, the later meal on the line under',
               repr(d.get('whatsapp')))
            d = json.loads(E_.get('/meal_plans/send/', {
                'view': 'week', 'date': '2031-11-26'}).content.decode())
            ok(d.get('period') == 'the week of 24 Nov to 30 Nov',
               'THE WEEK says which week', d.get('period'))
            d = json.loads(E_.get('/meal_plans/send/', {
                'view': 'day', 'date': '2031-11-25'}).content.decode())
            ok(d.get('period') == 'Tuesday 25 November' and
               d.get('days') == [] and d.get('empty'),
               'AN EMPTY DAY: named, and nothing in the list', d)
            # ---- A MOVE FOLLOWS THE MEAL TO ANOTHER PERIOD
            pie = MealEntry.objects.get(recipe__recipe_name='December pie')
            r = E_.post('/meal_plans/move/', {
                'meal_entry_id': pie.meal_entry_id, 'date': '2032-01-14',
                'view': 'month', 'from_date': '2031-12-01'})
            ok(r.status_code == 302 and 'date=2032-01-14' in r['Location']
               and 'view=month' in r['Location'],
               'MOVED TO JANUARY from December: the planner goes to January',
               r.get('Location'))
            r = E_.post('/meal_plans/move/', {
                'meal_entry_id': pie.meal_entry_id, 'date': '2032-01-20',
                'view': 'month', 'from_date': '2032-01-14'})
            ok('date=2032-01-14' in r['Location'],
               '  moved within the month on screen: you stay where you were',
               r.get('Location'))
            soup = MealEntry.objects.get(recipe__recipe_name='November soup')
            r = E_.post('/meal_plans/move/', {
                'meal_entry_id': soup.meal_entry_id, 'date': '2032-01-02',
                'view': 'week', 'from_date': '2031-12-29', 'dragged': '1',
                'order': str(soup.meal_entry_id)})
            ok('date=2031-12-29' in r['Location'] and 'view=week'
               in r['Location'],
               '  a drop across a week that spans two months stays on that '
               'week - the meal is on screen', r.get('Location'))
            r = E_.post('/meal_plans/move/', {
                'meal_entry_id': soup.meal_entry_id, 'date': '2031-11-24',
                'view': 'month', 'from_date': '2032-01-02', 'undo': '1'})
            ok('date=2031-11-24' in r['Location'],
               '  and an Undo back into November follows it there',
               r.get('Location'))
            raise Rollback
    except Rollback:
        pass

head('4. HELP AND REGISTERED')
g = read(GUIDE)
ok('the planner goes there with it' in g,
   'HELP: a moved meal takes the planner with it to another month')
ok('including one you reached with the arrows' in g and
   '<strong>What will be sent</strong>' in g,
   'HELP: Sending a plan says which period, and how it is shown')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
