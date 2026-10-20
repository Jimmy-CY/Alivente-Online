# -*- coding: utf-8 -*-
"""test_list_range.py - round SL-7, 20 Oct 2026.

THE SHOPPING LIST COVERS WHAT YOU ARE LOOKING AT.

Demetri: "We must also be able to select a day, or a couple of days or
a week for the Shopping List..." - and "a from/to range" when asked
which of those a couple of days meant.

The server has taken ?from= and ?to= since MN-1. What was wrong was
one line of markup: the button was hard-wired to the week, on a screen
that has had three views since MV-1.

WHY SECTION 3 ASKS THE THREE VIEWS RATHER THAN READING THE TEMPLATE.

The template no longer spells the dates - the view computes them - so
reading the markup proves only that it uses two context keys. What
matters is which DATES come out, and the only way to know is to ask
each view for its page and read the link.

AND THE MONTH IS THE MONTH. Month view draws whole weeks, so its grid
holds up to six days of the neighbouring months. A list for October
that quietly bought for 28 September would be a control that lies, so
the range is the 1st to the last and section 3 checks both ends.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. All three views answered, the week as the fallback,
      the button reading the computed pair, and a from/to pair on the
      list page that does not print.

  2   THE CONTROL. Re-asked of the pre-round files, where the link was
      the week whatever you were looking at.

  3   THE THREE LINKS, ASKED OF THE SERVER.

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

SUFFIX = '.bak_listrange'
ME = 'test_list_range.py'
PATCHER = 'apply_list_range.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'SL-7, 20 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
SL = os.path.join(ROOT, 'pages', 'templates',
                  'meal_plan_shopping_list.html')
GATE = os.path.join(ROOT, PS1)
FILES = (VIEW, TPL, SL)

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
    s = T.code_only(bundle[SL])
    c = {}
    c['THE RANGE IS DECIDED BESIDE THE VIEW - the finding'] = (
        "'sl_from': sl_from" in v and "'sl_to': sl_to" in v)
    c['the month is answered'] = ("view_mode == 'month'" in v)
    c['the day is answered'] = ("view_mode == 'day'" in v)
    c['and the week is the fallback'] = (
        'sl_from, sl_to = week_start, week_end' in v)
    # THE MONTH IS THE MONTH, NOT THE GRID. Built from day 1 rather
    # than from the first cell of a grid that draws whole weeks.
    c['the month runs 1st to last, not the grid it is drawn on'] = (
        'date(anchor.year, anchor.month, 1)' in v)
    c['the button reads the pair'] = ('sl_from' in t and 'sl_to' in t)
    c['and no longer hard-wires the week'] = (
        '?from={{ week_start' not in t)
    c['the list page can change its mind'] = (
        s.count('name="from"') == 1 and s.count('name="to"') == 1)
    c['with a GET, which is what the server reads'] = (
        'method="get"' in s)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# AND THE PAIR DOES NOT PRINT. SL-1 hides the chrome on paper and this
# belongs with it - a list on the fridge does not need a form on it.
SLC = T.code_only(NOW[SL])
pr = SLC.split('@media print', 1)
ok(len(pr) > 1 and '.sl-range' in pr[1][:900],
   'and it is hidden on paper, with the rest of the chrome')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok('THE RANGE IS DECIDED BESIDE THE VIEW - the finding' not in held,
   'CONTROL: before this round nothing computed a range',
   'what held: %r' % (held,))
OLDT = T.code_only(BEFORE[TPL])
ok('?from={{ week_start' in OLDT,
   'CONTROL: the link really was hard-wired to the week')
ok(T.code_only(BEFORE[SL]).count('name="from"') == 0,
   'CONTROL: and the list page had no way to change it')
# THE SERVER WAS ALREADY RIGHT, which is the point: this round is
# markup and one calculation, not a new aggregation path.
OLDV = T.python_code_only(BEFORE[VIEW], payloads=True)
ok("request.GET.get('from')" in OLDV and "request.GET.get('to')" in OLDV,
   'CONTROL: the server has taken from and to since MN-1 - nothing '
   'about the aggregation changes here')


# ==========================================================================
head('3. THE THREE LINKS, ASKED OF THE SERVER')
# ==========================================================================
seen, pair = {}, None
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
    from django.urls import reverse
    u = User.objects.create_user(username='sl7', password='x',
                                 email='sl7@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)
    # TUESDAY THE 20th OF OCTOBER, so every answer is distinguishable:
    # the month is 1-31, the week is 19-25, the day is 20-20.
    for v in ('month', 'week', 'day'):
        h = cl.get('/meal_plans/', {'view': v,
                                    'date': '2026-10-20'}
                   ).content.decode('utf-8')
        m = re.search(r'href="[^"]*\?from=([0-9-]+)&amp;to=([0-9-]+)"', h)
        seen[v] = (m.group(1), m.group(2)) if m else None
    h = cl.get(reverse('meal_shopping_list'),
               {'from': '2026-10-20', 'to': '2026-10-22'}
               ).content.decode('utf-8')
    pair = (re.search(r'id="slFrom"[^>]*value="([^"]*)"', h).group(1),
            re.search(r'id="slTo"[^>]*value="([^"]*)"', h).group(1))
except Exception as e:
    skip('the asked checks',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if not seen:
    skip('the links', 'nothing was asked')
else:
    print('')
    print('  anchor 2026-10-20, a Tuesday:')
    for v in ('month', 'week', 'day'):
        print('    %-6s %s' % (v, seen.get(v)))
    print('  the list page, asked for Tue-Thu: %s' % (pair,))
    print('')
    ok(seen.get('month') == ('2026-10-01', '2026-10-31'),
       'THE MONTH buys for the month - the 1st to the 31st, not the '
       'grid, which starts on 28 September', seen.get('month'))
    ok(seen.get('week') == ('2026-10-19', '2026-10-25'),
       'THE WEEK buys for the week on screen', seen.get('week'))
    ok(seen.get('day') == ('2026-10-20', '2026-10-20'),
       'THE DAY buys for that one day', seen.get('day'))
    # THE FINDING, IN ONE LINE: they are three different answers.
    ok(len(set(seen.values())) == 3,
       'and the three views give three different ranges - before this '
       'round all three gave the week', sorted(seen.values()))
    if pair:
        ok(pair == ('2026-10-20', '2026-10-22'),
           'and the list page holds an arbitrary pair - "a couple of '
           'days", which no view can express', pair)


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
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_viewswitch']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose view_mode it reads - so revert '
       'takes them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_list_range as PATCH                            # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
