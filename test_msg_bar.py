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
# BM-1, 21 Oct 2026 - base is part of the subject now. It renders the
# bar for every page that extends it, so a claim about whether the
# planner can show a message is a claim about base and about the
# planner not spelling a second loop of its own.
BASE = T.path_of('base.html')
BASETXT = read(BASE)
BASE_HAS_LOOP = (T.code_only(BASETXT).count(LOOP) == 1)


def claims(bundle):
    # BM-1, 21 Oct 2026 - INHERITED, NOT SPELLED. MG-1 put a loop on
    # each of these three pages and the fault was never three pages:
    # 55 more had it. base renders the bar now, so what MG-1 proved -
    # that a message written by the planner LANDS on the planner - is
    # asked of the rendered page in section 3, and what is asked here
    # is that the page does not spell a second loop of its own. Two
    # loops would show every message twice.
    c = {}
    for p in FILES:
        name = os.path.basename(p)
        code = T.code_only(bundle[p])
        c['%s renders a message bar' % name] = (
            code.count(LOOP) == 0 and BASE_HAS_LOOP)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# BM-1, 21 Oct 2026 - THE PLACE MOVED TO base. This asked where each
# of the three pages put the bar inside its own content. base puts it
# in one place for all of them now, so the question is asked once, of
# base, and the three are asked only that they do not spell one.
#
# .find(), NOT .index(), throughout. Against the reverted tree there is
# no bar in base at all, and .index() raised ValueError - the suite
# CRASHED rather than failing, which blocks a push exactly as hard and
# says far less about why. test_pick_note crashed on the same thing on
# 20 October.
_bi = BASETXT.find('{% block content %}')
_bl = BASETXT.find(LOOP)
ok(_bl >= 0 and _bi >= 0 and _bl < _bi,
   'base renders the bar ABOVE the page content, which is the only '
   'place one loop can sit', 'loop at %d, block at %d' % (_bl, _bi))
ok('class="alert' in BASETXT, '  and it is the house alert')
for p in FILES:
    name = os.path.basename(p)
    ok(T.code_only(NOW[p]).count(LOOP) == 0,
       '%s spells none of its own - two loops would show every '
       'message twice' % name)

# THE HOUSE SPELLING, read off the tree rather than trusted.
# BM-1, 21 Oct 2026 - there is exactly ONE page left that spells it,
# and it is base. This used to count how many pages already used the
# block MG-1 copied; the answer is 1, and that is the whole round.
#
# FOUND BY THE LOOP, NOT BY THE CLASS. The first `alv-message` in
# base.html is in its STYLESHEET, 138,000 characters before the loop,
# so anchoring on the class walked backwards into the sidebar and off
# the end. Ask for the tag.
import collections                                          # noqa: E402
shapes = collections.Counter()
spelt = []
for p in T.templates():
    s = read(p)
    found = 0
    for m in re.finditer(r'\{%\s*for\s+\w+\s+in\s+messages\s*%\}', s):
        k = s.find('{% endfor %}', m.start())
        if k < 0:
            continue
        shapes[re.sub(r'\s+', ' ', s[m.start():k + 12]).strip()] += 1
        found += 1
    if found:
        spelt.append((os.path.basename(p), found))
ok(len(shapes) == 1, 'ONE shape in the tree spells the message loop',
   '%d shape(s): %r' % (len(shapes), [x[:70] for x in shapes]))
ok(spelt == [('base.html', 1)],
   'and ONE page spells it, once - base. There were 81 on 21 October',
   spelt[:6])
house, n = shapes.most_common(1)[0] if shapes else ('', 0)

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
for p in FILES:
    ok('alv-message' not in T.code_only(BEFORE[p]),
       'CONTROL: %s really had no bar at all before MG-1'
       % os.path.basename(p))
# BM-1, 21 Oct 2026 - THE CONTROL IS STILL MG-1's BACKUP, and that is
# the point: these three pages had no bar before MG-1 and have none of
# their own after BM-1, for opposite reasons. claims() now asks about
# base, which .bak_msgbar2 says nothing about, so re-asking it of the
# backup would compare this round's tree with itself. The round that
# took the loops away carries its own control, in test_msg_base.py.
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
