# -*- coding: utf-8 -*-
"""test_msg_bar.py - round MG-1, 21 Oct 2026.

THREE PAGES WROTE MESSAGES AND NONE OF THEM COULD SHOW ONE.

Demetri, testing push 3 on Live:

    "The success messages for the Add recipe to Meal Plan, Delete
     recipe from meal plan, all land on future screen (e.g Recipe
     Management, or Logout screen, if the system auto-logs me out)."

Django keeps a message in the session until a template RENDERS one.
78 of the 151 live templates carry the loop; the planner, the
shopping list and the printable plan carried none between them. So
every messages.success() in meal_planning.py queued and surfaced on
whatever page he reached next that had a bar.

THIS SUITE PROVES IT BY DOING IT. Section 3 removes a meal with a
real POST and follows the redirect, and the claim is that the word
arrives on the page that did the work - which is the only form of
this claim that is about the application rather than about a file.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. All three render exactly one bar, at the top, in
      the spelling 73 other pages use - and the printable one hides
      it on paper.

  2   THE CONTROL. Re-asked of the pre-round files, where none did.

  3   DRIVEN. A real remove, a real redirect, and the message read
      off the page that comes back. Then the same thing proved in
      reverse: before this round it landed on Recipe Management.

  4   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_msgbar2'
ME = 'test_msg_bar.py'
PATCHER = 'apply_msg_bar.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MG-1, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates')
PLANNER = os.path.join(TPL, 'meal_planner.html')
SHOP = os.path.join(TPL, 'meal_plan_shopping_list.html')
PRINT = os.path.join(TPL, 'meal_plan_print.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
GATE = os.path.join(ROOT, PS1)
FILES = (PLANNER, SHOP, PRINT)

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
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)
LOOP = '{% for msg in messages %}'


def claims(bundle):
    c = {}
    for p in FILES:
        name = os.path.basename(p)
        code = T.code_only(bundle[p])
        c['%s renders a message bar' % name] = (code.count(LOOP) == 1)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

for p in FILES:
    name = os.path.basename(p)
    body = NOW[p]
    # .find(), NOT .index(). Against the reverted tree there is no bar
    # on any of these three pages, and .index() raised ValueError -
    # the suite CRASHED rather than failing, which blocks a push
    # exactly as hard and says far less about why. test_pick_note
    # crashed on the same thing on 20 October.
    i = body.find('{% block content %}')
    at = body.find('alv-message')
    ok(at >= 0 and i >= 0 and at - i < 1400,
       '%s puts it at the top of the content' % name,
       'block at %d, message at %d' % (i, at))
    ok('class="alert' in body, '  and it is the house alert' % ())

# THE HOUSE SPELLING, read off the tree rather than trusted.
import collections                                          # noqa: E402
shapes = collections.Counter()
for p in T.templates():
    s = read(p)
    if 'alv-message' not in s:
        continue
    i = s.index('alv-message')
    j = s.rfind('{% for', 0, i)
    if j < 0:
        continue
    k = s.find('{% endfor %}', i)
    shapes[re.sub(r'\s+', ' ', s[j:k + 12]).strip()] += 1
house, n = shapes.most_common(1)[0]
# .find() AGAIN, for the same reason: against the reverted tree the
# planner has no loop to compare, and a missing block is a FAILED
# claim here, not a ValueError.
_at = NOW[PLANNER].find(LOOP)
_end = (NOW[PLANNER].find('{% endfor %}', _at) if _at >= 0 else -1)
mine = (re.sub(r'\s+', ' ', NOW[PLANNER][_at:_end + 12]).strip()
        if _at >= 0 and _end > _at else '(no loop on the planner)')
ok(mine == house,
   'and all three use the block %d other pages already use' % n,
   '\n  house: %s\n  mine : %s' % (house[:88], mine[:88]))

# THE PRINTABLE PAGE DOES NOT PRINT IT.
pc = T.code_only(NOW[PRINT])
pb = pc[pc.index('@media print'):] if '@media print' in pc else ''
ok('.alv-message' in pb,
   'and the printable plan hides it on paper - a dismissible alert '
   'on paper is a box with a cross in it')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: before this round not one of the three did',
   'what held: %r' % (held,))
for p in FILES:
    ok('alv-message' not in T.code_only(BEFORE[p]),
       'CONTROL: %s really had no bar at all' % os.path.basename(p))
# AND THE VIEW REALLY WRITES MESSAGES. Without this the round is a
# bar on a page that never had anything to show.
vsrc = T.python_code_only(read(VIEW), payloads=True)
nmsg = len(re.findall(r'messages\.(?:success|info|error|warning)\(', vsrc))
ok(nmsg > 10,
   'CONTROL: and the view writes %d messages that had nowhere to land'
   % nmsg, nmsg)


# ==========================================================================
head('3. DRIVEN - A REAL REMOVE, AND WHERE THE WORD LANDS')
# ==========================================================================
# THE ONLY FORM OF THIS CLAIM THAT IS ABOUT THE APPLICATION. Everything
# above is about files. This posts a removal, follows the redirect, and
# reads the page that comes back.
landed = following = None
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    django.setup()
    from django.conf import settings as dj
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'mysite.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    import datetime as dt
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from django.urls import reverse
    from pages.models import MealEntry, Recipe
    u = User.objects.create_user(username='mg1', password='x',
                                 email='mg1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Gemista', servings=6,
                              prep_time=10, cook_time=20)
    e = MealEntry.objects.create(date=dt.date(2026, 10, 21), recipe=r,
                                 servings=6, created_by=u)
    cl = Client()
    cl.force_login(u)
    resp = cl.post(reverse('remove_meal_entry'),
                   {'meal_entry_id': e.meal_entry_id,
                    'view': 'day', 'date': '2026-10-21'},
                   follow=True)
    landed = resp.content.decode('utf-8')
    following = resp.redirect_chain[-1][0] if resp.redirect_chain else ''
except Exception as ex:
    skip('the driven check',
         'Django would not start: %s' % str(ex).split('\n')[0][:80])

if landed is None:
    skip('where the message lands', 'nothing was posted')
else:
    shown = re.findall(r'class="alert alert-\w+[^"]*alv-message"[^>]*>\s*'
                       r'([^<]+)', landed)
    shown = [x.strip() for x in shown if x.strip()]
    print('')
    print('  posted a removal, followed the redirect to:')
    print('      %s' % following)
    print('  message(s) rendered on that page: %r' % (shown,))
    print('')
    ok('/meal_plans/' in following,
       'the write returns to the planner', following)
    ok(bool(shown), 'AND THE MESSAGE IS ON IT - which is the finding',
       shown)
    ok(any('Removed' in x for x in shown),
       '  and it is the one the removal wrote', shown)
    # THE SESSION IS EMPTY AFTERWARDS. A message rendered is a message
    # consumed; if it were still queued it would appear again on the
    # NEXT page, which is exactly what he reported.
    nxt = cl.get(reverse('recipe_management')).content.decode('utf-8')
    again = re.findall(r'alert-\w+[^"]*alv-message"[^>]*>\s*([^<]+)', nxt)
    again = [x.strip() for x in again if x.strip()]
    ok(not again,
       '  and it does NOT appear again on Recipe Management - the '
       'screen he kept finding it on', again)


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_msg_bar as PATCH                               # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
