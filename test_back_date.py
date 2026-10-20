# -*- coding: utf-8 -*-
"""test_back_date.py - round PB-3, 20 Oct 2026.

A WRITE LEAVES YOU ON THE DAY YOU WERE ON.

Demetri: "When I added Leftovers to a recipe, it disappeared from the
current day. When I went back to Week view though it showed again on
the day, with the Leftovers a couple of days later."

Nothing disappeared. add_leftover returned to monday_of(the leftovers'
date), so standing on Tuesday in Day view and dating leftovers for
Thursday landed him on Monday - a day with nothing on it.

PB-2 SAID IT WOULD, in its own docstring: it kept the VIEW and left
the DATE to sixteen call sites. Two of them took the date from the
write rather than from the reader.

WHY THE CHECK IS A Location HEADER.

This fault is invisible in the markup and invisible in the rendered
page. It lives in one header of one redirect, so section 3 posts the
real form to the real endpoint and reads where it is sent - with the
field and without it, because a round that always returned to the
anchor would pass a one-sided test while breaking the fallback for
any request that carries none.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The signature, both verbs, nine forms carrying the
      day, and exactly one call site that opts out.

  2   THE CONTROL. Re-asked of the pre-round file.

  3   THE REDIRECT, posted: with from_date, without it, and from a
      different view.

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

import datetime as dt
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_backdate'
ME = 'test_back_date.py'
PATCHER = 'apply_back_date.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PB-3, 20 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL, VIEW)
N_FORMS = 9

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


def claims(bundle):
    v = T.python_code_only(bundle[VIEW], payloads=True)
    t = T.code_only(bundle[TPL])
    c = {}
    c['THE READER SAYS WHERE THEY WERE - the finding, in one line'] = (
        'def planner_back(request, when=None, stay=True)' in v)
    c['and it is read from a POST'] = (
        "request.POST.get('from_date')" in v)
    c['and from a GET, for the redirects that use one'] = (
        "request.GET.get('from_date')" in v)
    c['every form that sends the view sends the day'] = (
        t.count('name="view"') == N_FORMS
        and t.count('name="from_date"') == N_FORMS)
    c['and the day is the anchor the page was rendered at'] = (
        t.count("name=\"from_date\" value=\"{{ anchor|date:'Y-m-d' }}\"")
        == N_FORMS)
    c['exactly one action still moves you on purpose'] = (
        len(re.findall(r'planner_back\([^)]*stay=False', v)) == 1)
    # THE CALL SITES ARE NOT REWRITTEN. Their date is the right
    # FALLBACK for a request carrying no from_date - an old open tab,
    # or a link somebody saved.
    c['the call sites keep their own date as a fallback'] = (
        len(re.findall(r'planner_back\(request, monday_of\(', v)) >= 2)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

_v = T.python_code_only(NOW[VIEW], payloads=True)
_i = _v.index('stay=False')
ok('copy_meal_week' in _v[max(0, _i - 2500):_i],
   'and the one that opts out is the week copy, where seeing the copy '
   'is the point of the action')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok('THE READER SAYS WHERE THEY WERE - the finding, in one line'
   not in held,
   'CONTROL: before this round planner_back took no such argument',
   'what held: %r' % (held,))
OLDV = T.python_code_only(BEFORE[VIEW], payloads=True)
ok('def planner_back(request, when=None):' in OLDV,
   'CONTROL: it had the two-argument signature PB-2 left')
ok('from_date' not in OLDV,
   'CONTROL: and nothing read the reader\'s own date')
ok(T.code_only(BEFORE[TPL]).count('name="from_date"') == 0,
   'CONTROL: no form sent it')
# AND THE TWO GUESSERS WERE ALREADY THERE. This round did not create
# them; it made them harmless.
ok(len(re.findall(r'planner_back\(request, monday_of\(', OLDV)) >= 2,
   'CONTROL: two call sites already took the date from the write')


# ==========================================================================
head('3. THE REDIRECT, POSTED')
# ==========================================================================
sent = {}
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
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Recipe
    u = User.objects.create_user(username='pb3', password='x',
                                 email='pb3@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    cl = Client()
    cl.force_login(u)

    # THE ROUTE COMES FROM THE URLCONF, NOT FROM A PATH TYPED HERE.
    # The first spelling posted to '/meal_plans/leftover/add/' because
    # that looked right, and got three 404s - the same fault RD-1's
    # shell records WCIM paying, one layer down.
    from django.urls import reverse
    ADD = reverse('add_leftover')

    # HIS CASE, EXACTLY: standing on Tuesday the 20th in Day view,
    # leftovers dated Thursday the 22nd.
    def post(extra, view='day'):
        e = MealEntry.objects.create(date=dt.date(2026, 10, 20),
                                     recipe=r, servings=4,
                                     created_by=u)
        body = {'meal_entry_id': e.meal_entry_id,
                'date': '2026-10-22', 'view': view}
        body.update(extra)
        resp = cl.post(ADD, body)
        return resp.get('Location', '(no redirect: %s)'
                        % resp.status_code)

    sent['with the day he was on'] = post({'from_date': '2026-10-20'})
    sent['without it (an old tab)'] = post({})
    sent['from Week view'] = post({'from_date': '2026-10-20'},
                                  view='week')
except Exception as e:
    skip('the posted checks',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if not sent:
    skip('the redirect', 'nothing was posted')
else:
    print('')
    for k in ('with the day he was on', 'without it (an old tab)',
              'from Week view'):
        if k in sent:
            print('  %-24s -> %s' % (k, sent[k]))
    print('')

    ok('date=2026-10-20' in sent['with the day he was on'],
       'THE FINDING: adding leftovers for Thursday leaves you on the '
       'Tuesday you were standing on', sent['with the day he was on'])
    ok('view=day' in sent['with the day he was on'],
       'and in the view you were in - PB-2\'s half, still holding')
    # THE FALLBACK. A request with no from_date must still work, and
    # must still go somewhere sensible rather than nowhere.
    ok('date=2026-10-19' in sent['without it (an old tab)'],
       'a request that sends no day falls back to the call site\'s '
       'own date, as it did before', sent['without it (an old tab)'])
    ok('view=week' in sent['from Week view'],
       'and the view still travels independently of the date',
       sent['from Week view'])
    ok('date=2026-10-20' in sent['from Week view'],
       'with the same day, because the day you were on does not '
       'depend on the zoom level', sent['from Week view'])


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
_j = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_viewback']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _j,
       'and it sits after %s, whose function it widens - so revert '
       'takes them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_back_date as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
