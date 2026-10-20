# -*- coding: utf-8 -*-
"""test_planner_back.py - round PB-2, 19 Oct 2026.

RELEASE 4, PUSH 2. A WRITE ON THE PLANNER LEAVES YOU WHERE YOU WERE.

THE REGRESSION THIS SUITE EXISTS BECAUSE OF, and the reason it drives
rather than reads: push 1 shipped eleven redirects that carried the
date and dropped the view, so every add, every remove, every note and
every copied week handed you the Month however you had got there. It
was found by DRIVING the endpoints, not by reading them - the code
looks entirely reasonable until you ask it where it sent you.

    action, performed while in Day view        where you landed
    -----------------------------------------------------------
    remove a meal                              Month
    add a meal (from Week view)                Month

AND MV-1 HAD ALREADY FIXED THIS ONCE. Its docstring says so, about
the JavaScript: "goWeek and goMonth build their own address and
NEITHER CARRIED THE VIEW ... a control that is tested only against
itself is tested against the half that was never in doubt." One
plannerUrl() fixed that half. Its suite then drove the three switcher
links and the week arrows - the half that had just been fixed - and
never asked the server redirects anything at all.

SO THIS SUITE'S SECTION 3 IS A MATRIX, not a sample. Every endpoint
that returns to the planner, driven from every one of the three
views, with the landing view read back off the Location header. If
that is more rows than feel necessary, so was the push that went out
without them.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One function builds the return address; no endpoint
      spells one by hand; the form is read before the Referer; and
      every form on the page carries the view.

  2   THE CONTROL. Every claim re-asked of the pre-round files, where
      eleven addresses are built by hand and not one carries a view.

  3   DRIVEN, as a matrix. Each endpoint x each view, and the view
      read back off the redirect.

  4   THE FALLBACK, on its own. A post with no view field at all, from
      a page whose Referer says Week - because a form can be submitted
      by code that forgot, and the answer should still not be Month.

  5   Scope, registration and the gate.

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

SUFFIX = '.bak_viewback'
ME = 'test_planner_back.py'
PATCHER = 'apply_planner_back.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PB-2, 19 Oct 2026'
# WHAT THE ROUND REWROTE, and what the tree holds NOW - two numbers,
# because later rounds in the same push added to both.
#
#   PB-2 found and rewrote 11 return addresses and put the hidden view
#   on 8 forms. RD-2 then added move_meal_entry, which returns to the
#   planner from five places, and a Move dialog with a form of its own.
#
# A number may only move when the thing it counts really grew, and
# this one did: 11 -> 16 and 8 -> 9, by one named round.
N_REWROTE = 11
N_REDIRECTS = 16
N_FORMS = 9
VIEWS = ('month', 'week', 'day')

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FILES = (VIEW, TPL)

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
    """Every source claim PB-2 makes, written once and asked twice."""
    v = T.python_code_only(bundle[VIEW], payloads=True)
    t = T.code_only(bundle[TPL])
    c = {}

    c['one function builds the return address'] = (
        'def planner_back(' in v)
    c['and one reads which view you were in'] = (
        'def planner_view(' in v)
    # THE CALLS, NOT THE DECLARATION. `planner_back(request` matches
    # `def planner_back(request, ...)` too, and the patcher's own gate
    # counted 12 and refused the round over the function it had just
    # written.
    c['all %d return addresses go through it' % N_REDIRECTS] = (
        len(re.findall(r'(?<!def )planner_back\(request', v))
        == N_REDIRECTS)
    c['and not one still builds an address by hand'] = (
        bool(v) and '?week=%s' not in v)

    # THE FORM IS ASKED BEFORE THE REFERER. A Referer is
    # attacker-settable and a proxy may strip it; the form is neither.
    c['the posted form is read first'] = (
        "request.POST.get('view')" in v)
    c['and the Referer only as a fallback'] = (
        'HTTP_REFERER' in v and
        v.find("request.POST.get('view')") < v.find('HTTP_REFERER'))
    c['a view that is not one of the three is discarded'] = (
        'PLANNER_VIEWS' in v and 'in PLANNER_VIEWS' in v)

    c['every form on the planner carries the view'] = (
        t.count('<input type="hidden" name="view"') == N_FORMS)

    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)


# ==========================================================================
head('2. THE CONTROL - every claim re-asked of the pre-round files')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
WAS_CLAIMS = claims(BEFORE)
held = [m for m, got in WAS_CLAIMS.items() if got]
ok(not held,
   'not one of the %d claims held before this round ran' % len(WAS_CLAIMS),
   'these held already: %r' % (held[:4],))

OLD_V = T.python_code_only(BEFORE[VIEW], payloads=True)
ok(OLD_V.count('?week=%s') == N_REWROTE,
   'CONTROL: there really were %d addresses built by hand when this '
   'round ran - the other %d arrived with RD-2, already using the '
   'helper' % (N_REWROTE, N_REDIRECTS - N_REWROTE),
   'count was %d' % OLD_V.count('?week=%s'))
ok('&view=' not in OLD_V and "'?view=" not in OLD_V,
   'CONTROL: and not one of those addresses carried a view - which is '
   'the regression, stated as a fact about the old file')
ok(T.code_only(BEFORE[TPL]).count(
    '<input type="hidden" name="view"') == 0,
   'CONTROL: and no form sent the view at all')


# ==========================================================================
head('3. DRIVEN - every endpoint, from every view')
# ==========================================================================
django_up = False
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import alv_offline                                      # noqa: F401
    import django
    django.setup()
    from django.conf import settings as dj_settings
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj_settings.ROOT_URLCONF = 'mysite.urls'
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + \
        ['testserver']
    dj_settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher']
    dj_settings.DEBUG = True
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if not django_up:
    skip('the matrix', 'no database')
else:
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from django.urls import reverse
    from pages.models import MealEntry, Recipe

    u = User.objects.create_user(username='pb2', password='x',
                                 email='pb2@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(
                Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)

    recipe = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    WED = dt.date(2026, 10, 21)
    MON = dt.date(2026, 10, 19)

    def landed(resp):
        """Which view the redirect sends you to - read, not assumed.

        AND AN ABSENT view IS 'month', not 'none'. That is the whole
        regression: meal_planner falls back to Month when the
        parameter is missing, so a redirect that merely forgets it
        lands you there just as surely as one that said so.
        """
        loc = resp.get('Location') or ''
        got = re.search(r'[?&]view=(\w+)', loc)
        return got.group(1) if got else 'month'

    def fresh_entry():
        return MealEntry.objects.create(date=WED, recipe=recipe,
                                        servings=4, created_by=u)

    # EACH ROW IS AN ENDPOINT AND HOW TO POST TO IT. The payload is
    # built fresh per view, because several of them consume a row.
    def cases(view):
        return [
            ('remove_meal_entry',
             lambda: {'meal_entry_id': fresh_entry().meal_entry_id,
                      'view': view}),
            ('add_meal_entry',
             lambda: {'recipe_id': recipe.recipe_id,
                      'date': WED.strftime('%Y-%m-%d'),
                      'servings': '4', 'view': view}),
            ('add_meal_note',
             lambda: {'date': WED.strftime('%Y-%m-%d'),
                      'note': 'Eat out', 'view': view}),
            ('add_leftover',
             lambda: {'meal_entry_id': fresh_entry().meal_entry_id,
                      'date': (WED + dt.timedelta(days=1)).strftime(
                          '%Y-%m-%d'),
                      'view': view}),
            ('copy_meal_week',
             lambda: {'from_week': MON.strftime('%Y-%m-%d'),
                      'to_week': (MON + dt.timedelta(days=7)).strftime(
                          '%Y-%m-%d'), 'view': view}),
            ('save_menu',
             lambda: {'week': MON.strftime('%Y-%m-%d'),
                      'name': 'Week of lentils', 'view': view}),
        ]

    print('  %-22s %-8s %-8s %-8s' % ('endpoint', 'month', 'week', 'day'))
    print('  ' + '-' * 50)
    bad = []
    for name, _ in cases('month'):
        row = []
        for view in VIEWS:
            maker = [c[1] for c in cases(view) if c[0] == name][0]
            try:
                resp = cl.post(reverse(name), maker())
            except Exception as exc:
                row.append('ERR')
                bad.append((name, view, 'raised %s' % str(exc)[:40]))
                continue
            if resp.status_code not in (302, 301):
                row.append('%s' % resp.status_code)
                bad.append((name, view, 'status %s' % resp.status_code))
                continue
            got = landed(resp)
            row.append(got)
            if got != view:
                bad.append((name, view, got))
        print('  %-22s %-8s %-8s %-8s' % (name, row[0], row[1], row[2]))
    print('')

    ok(not bad,
       'every endpoint, from every view, sends you back to that view',
       'these did not: %r' % (bad[:6],))

    # AND THE DATE STILL SURVIVES. The old address carried it and this
    # round must not have traded one for the other.
    e = fresh_entry()
    resp = cl.post(reverse('remove_meal_entry'),
                   {'meal_entry_id': e.meal_entry_id, 'view': 'day'})
    loc = resp.get('Location') or ''
    ok('date=2026-10-21' in loc,
       'and the date comes back too, which the old address already did',
       'Location was %r' % loc)

    # A VIEW NOBODY RECOGNISES IS DISCARDED, not reflected. `?view=` is
    # a string somebody can type, and a template that branches on it
    # renders nothing at all for a value it does not know - A5.
    e = fresh_entry()
    resp = cl.post(reverse('remove_meal_entry'),
                   {'meal_entry_id': e.meal_entry_id,
                    'view': 'month"><script>'})
    ok(landed(resp) == 'month',
       'a view nobody recognises comes back as Month, not reflected',
       'landed on %r' % landed(resp))


# ==========================================================================
head('4. THE FALLBACK, ASKED ON ITS OWN')
# ==========================================================================
if not django_up:
    skip('the fallback', 'no database')
else:
    # A FORM MAY FORGET. The hidden field is the primary path and the
    # matrix above proves it; this proves the other one, because a
    # fallback that is never exercised is a fallback nobody knows is
    # broken.
    e = fresh_entry()
    resp = cl.post(
        reverse('remove_meal_entry'), {'meal_entry_id': e.meal_entry_id},
        HTTP_REFERER='/meal_plans/?view=week&date=2026-10-21')
    ok(landed(resp) == 'week',
       'with no view on the form, the Referer answers')

    e = fresh_entry()
    resp = cl.post(reverse('remove_meal_entry'),
                   {'meal_entry_id': e.meal_entry_id})
    ok(landed(resp) == 'month',
       'and with neither, Month - which is where you land today, and '
       'is the right answer when nothing knows better')

    # THE FORM BEATS THE REFERER. They can disagree - a page left open
    # in one view while another tab moved on - and the form is the one
    # that was actually submitted.
    e = fresh_entry()
    resp = cl.post(
        reverse('remove_meal_entry'),
        {'meal_entry_id': e.meal_entry_id, 'view': 'day'},
        HTTP_REFERER='/meal_plans/?view=week&date=2026-10-21')
    ok(landed(resp) == 'day',
       'and when the two disagree, the form wins')


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
# AFTER WHAT IT BUILDS ON, not "newest".
#
# This asserted ROUNDS[-1] == SUFFIX, which is true of a round
# delivered on its own and FALSE for seven of the eight in this push -
# only one of them can be last. Eight suites carried the same wrong
# claim, because each was written as though it would ship alone.
#
# The claim was reaching for something real: revert runs NEWEST FIRST,
# so a round must sit AFTER anything whose work it edits, or reverting
# the two in order restores the older round's text over the newer
# one. That is the 18 Oct bug and it cost a hand repair.
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in []:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose work it edits - so revert takes '
       'them off in the right order' % _dep)
# RETIRED - DB-1, 20 Oct 2026. This asked whether the round sat in
# the last eight entries of the register, which was true while push 2
# was the newest thing in it and false as soon as anything shipped
# after it. It is the same mistake as the `ROUNDS[-1] == SUFFIX` it
# replaced: a claim about a POSITION in a growing list expires
# whatever number is in it, so re-pinning would only move the date.
# The dependency claim above is the real one and does not expire.
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once',
   alv_rounds.ROUNDS.count(SUFFIX))
ok('def planner_back(' in gate, 'the gate pins the one place')

for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))

patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok(MARK in NOW[VIEW], 'and so does the helper it wrote')
ok('already applied' in patcher,
   'the patcher has an already-applied path')
import apply_planner_back as PATCH                          # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
