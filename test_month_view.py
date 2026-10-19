# -*- coding: utf-8 -*-
"""test_month_view.py - round MV-2, 19 Oct 2026.

RELEASE 4, PUSH 1. THE MONTH IS THE VIEW.

Demetri, testing the live planner: "why does this still have the time
calendar?" - about the 320px mini calendar beside the week. And on the
design: "Monthly Calendar first - full page."

THIS SUITE RENDERS THE CALENDAR, and that is not a formality. MC-4 is
the round where every class name on the mini calendar was correct and
the thing drew THIRTY-FIVE CELLS IN ONE COLUMN on the live site, for
four weeks, because the grid closed before the loop that filled it.
Two checks asserted the right strings were in the markup and both
passed every day it was broken. A layout fault is only in the picture.

So section 3 opens the month in a browser and counts COLUMNS.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One query for the month fetching meals; three names
      then a count; one grid with its headings inside it and no row
      wrapper; a cell that is a button the keyboard can reach.

  2   THE CONTROL. Every claim re-asked of the pre-round files, where
      the month was a strip of dots beside a week.

  3   RENDERED, at 1200 and at 390. Seven distinct column positions,
      five or six rows, names at full size and marks on the phone -
      and the page not wider than itself.

  4   WIDE. The component is gone from the whole tree, markup and
      stylesheet, because a selector that matches nothing is a claim
      about the page that has stopped being true. This round tripped
      over one of those an hour before it was written.

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

SUFFIX = '.bak_monthview'
ME = 'test_month_view.py'
PATCHER = 'apply_month_view.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MV-2, 19 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
FILES = (VIEW, TPL)

# THE MINI CALENDAR'S WHOLE VOCABULARY. Named here rather than
# guessed, so a class this round forgot shows as a failure and not as
# a quiet survival.
# THE MINI CALENDAR'S WHOLE VOCABULARY, for this page.
GONE = ('mini-calendar', 'mini-calendar-grid', 'mini-calendar-week',
        'mini-calendar-day', 'mini-calendar-header', 'mini-calendar-nav',
        'left-panel', 'calendar-legend', 'legend-item', 'legend-dot',
        'calendar_weeks')

# AND THE SUBSET THIS COMPONENT OWNS OUTRIGHT.
#
# `legend-item` and `legend-dot` are NOT among them: four other pages
# use them - celebration_calendar, cashflow_forecast, lease_timeline
# and project_gantt - and the first cut of the wide check below
# declared them dead across the whole tree and accused all four. A
# class this page happened to use is not a class this page owns.
OURS = tuple(g for g in GONE
             if g.startswith('mini-calendar') or g in ('left-panel',
                                                       'calendar_weeks'))

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


def claims(text):
    """Every source claim MV-2 makes, written once and asked twice."""
    c = {}
    code = T.code_only(text[TPL])
    js = T.code_only_js(text[TPL])
    v = T.python_code_only(text[VIEW], payloads=True)

    # ---- 1. ONE query, and it fetches MEALS
    # ASKED OF THE MONTH QUERY, NOT OF THE MODULE. select_related on
    # the recipe and its parent was already true of the WEEK query
    # before this round, so asking the whole file answered a different
    # question and the control section said so. The slice is the
    # month's own query and nothing else.
    _m = v.split('month_by_date = {}')[-1].split('MONTH_SHOWN')[0] \
        if 'month_by_date = {}' in v else ''
    c['the month is gathered in one pass'] = (
        'month_by_date.setdefault' in _m)
    c['  fetching the meals, not a set of dates that have one'] = (
        bool(_m) and 'values_list' not in _m)
    c['  with the recipe and its parent joined  [E29]'] = (
        "select_related('recipe', 'leftover_of')" in _m)
    c['  in the order a day holds them'] = (
        "order_by('date', 'sort_order', 'meal_entry_id')" in _m)

    # ---- 2. three names, then a count
    c['a cell shows three names'] = 'MONTH_SHOWN = 3' in v
    c['  and counts the rest'] = (
        "'more': max(0, len(mine) - MONTH_SHOWN)" in v)
    c['  four marks at most, because a fifth wraps the row'] = (
        'MONTH_DOTS = 4' in v)
    c['  and the marks carry WHAT each meal is'] = (
        "'is-note' if not e.recipe_id" in v
        and "'is-leftover' if e.leftover_of_id" in v)
    c['the header counts the MONTH, not the week'] = (
        "'month_count': sum(len(v) for v in month_by_date.values())"
        in v)

    # ---- 3. ONE grid, headings inside it, no row wrapper  [MC-4]
    c['the month is a seven column grid'] = (
        '.month-grid {' in code
        and 'grid-template-columns: repeat(7, minmax(0, 1fr));' in code)
    c['  and the weekday headings are INSIDE it  [MC-4]'] = (
        code.count('class="month-dow"') == 7)
    c['  with no row wrapper to lose the cells to  [MC-4]'] = (
        'month-week' not in code
        and not re.search(r'display:\s*contents', code))

    # ---- 4. both pictures, and the stylesheet picks one
    c['a cell carries a name'] = 'class="month-chip' in code
    c['  and a mark'] = 'class="month-dots"' in code
    c['  the marks are hidden at full size'] = (
        '.month-dots {' in code
        and 'display: none;' in
        code.split('.month-dots {')[1].split('}')[0])
    c['  and the names below 768px, where five characters is noise'] = (
        '@media screen and (max-width: 767px)' in text[TPL]
        and '.month-chip,\n    .month-more {\n        display: none;'
        in text[TPL])

    # ---- 5. the cell is a button, and the keyboard reaches it
    c['a cell is a button'] = 'role="button" tabindex="0"' in code
    c['  that opens the picker on its own day  [Q2]'] = (
        "onclick=\"openPicker('{{ cell.date|date:'Y-m-d'|escapejs }}'"
        in code)
    c['  says which day, for a screen reader'] = (
        'aria-label="{{ cell.count }} meal{{ cell.count|pluralize }} on'
        in code)
    c['  and answers the keyboard'] = (
        '.month-cell[role="button"]' in js and "'Enter'" in js
        and "'keydown'" in js)
    # PAIRED WITH THE CELL EXISTING. A page with no month cell has no
    # onkeydown on one either, so the absence alone was true before.
    c['  delegated once, not once per cell'] = (
        'role="button" tabindex="0"' in code
        and code.count('onkeydown') == 0)

    # ---- 6. the layout gave up its first column
    c['the layout is one column'] = (
        '.calendar-layout {\n    display: block;\n}' in code)
    c['the week body is shown only when the month is not'] = (
        "{% if view_mode != 'month' %}" in code)

    # ---- 7. the component is GONE, markup and style
    for g in GONE:
        c['%s is gone' % g] = g not in code and g not in v
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
NOW_CLAIMS = claims(NOW)
for k in NOW_CLAIMS:
    ok(NOW_CLAIMS[k], k)


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the pre-round tree')
# ==========================================================================
WASC = claims(dict((p, was(p)) for p in FILES))
leaked = sorted(k for k in NOW_CLAIMS if WASC.get(k))
# NOT ONE OF THEM. Every claim this round makes was false before it,
# including the absences - because each is PAIRED with the thing whose
# absence it is about. The first cut of this section allowed four
# leaks and every one of them was a check asking the wrong question:
# three asked the whole module where they meant the month's own query,
# and one asked for an absence on a page that had nothing to be absent
# from.
ok(leaked == [],
   'NOT ONE claim was already true before MV-2 - every absence is '
   'paired with the thing it is an absence of', leaked)

BV = T.python_code_only(was(VIEW), payloads=True)
BC = T.code_only(was(TPL))
ok('dates_with_meals' in BV,
   'CONTROL: the month was a set of DATES THAT HAVE A MEAL - one '
   'boolean a day, which is all a dot needs')
ok('calendar_weeks' in BV and 'calendar_weeks' not in
   T.python_code_only(NOW[VIEW], payloads=True),
   'CONTROL: and calendar_weeks really was there to replace')
ok('mini-calendar' in BC,
   'CONTROL: the mini calendar really was in the markup')
ok('grid-template-columns: 320px 1fr;' in BC,
   'CONTROL: and the layout really did give it a 320px column - the '
   '207px that a month cell gets back')


# ==========================================================================
head('3. RENDERED - seven columns, and the page not wider than itself')
# ==========================================================================
# MC-4 IS WHY THIS SECTION EXISTS. Every class name on the old mini
# calendar was right and it drew one column for four weeks. Nothing
# above this line could have seen that.
django_up = False
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    from django.conf import settings as dj_settings
    django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections, reset_queries
    from asgiref.local import Local
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj_settings.ROOT_URLCONF = 'mysite.urls'
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + \
        ['testserver']
    dj_settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher']
    dj_settings.DEBUG = True           # connection.queries needs it
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a rendered month',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

body = ''
if django_up:
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Recipe

    u = User.objects.create_user(username='mv2', password='x',
                                 email='mv2@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(
                Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)

    NAMES = ['Fakes', 'Greek Salad (Horiatiki)', 'Moussaka', 'Pastitsio',
             'Souvlaki', 'Tzatziki', 'Salad - Butternut Squash Quinoa',
             'Baklava', 'Briam', 'Keftedes']
    rs = [Recipe.objects.create(recipe_name=n, servings=4)
          for n in NAMES]
    # A DAY WITH SIX ON IT, so "+n more" has something to count, and a
    # note and a leftover so the three colours are all in the picture.
    BUSY = dt.date(2026, 10, 21)
    parent = None
    for k, i in enumerate((3, 6, 8, 9, 4)):
        e = MealEntry.objects.create(date=BUSY, recipe=rs[i], servings=4,
                                     sort_order=k + 1, created_by=u)
        if parent is None:
            parent = e
    MealEntry.objects.create(date=BUSY, recipe=None, note='Angy away',
                             servings=0, sort_order=9, created_by=u)
    MealEntry.objects.create(date=dt.date(2026, 10, 22), recipe=rs[0],
                             servings=4, sort_order=1,
                             leftover_of=parent, created_by=u)
    for day in (2, 6, 13, 16, 19, 24, 28):
        MealEntry.objects.create(date=dt.date(2026, 10, day),
                                 recipe=rs[day % len(rs)], servings=4,
                                 sort_order=1, created_by=u)

    URL = '/meal_plans/planner/?view=month&date=2026-10-21'

    # ---- ONE QUERY FOR THE MONTH, measured before anything is drawn.
    reset_queries()
    resp = cl.get(URL)
    few = len(connections['default'].queries)
    ok(resp.status_code == 200, 'the month answers', resp.status_code)
    for day in range(1, 29):
        MealEntry.objects.create(date=dt.date(2026, 10, day),
                                 recipe=rs[day % len(rs)], servings=4,
                                 sort_order=7, created_by=u)
    reset_queries()
    resp = cl.get(URL)
    many = len(connections['default'].queries)
    ok(many <= few,
       'twenty-eight more meals cost %d queries against %d - the month '
       'is ONE pass, not one per day  [E29]' % (many, few), (few, many))

    body = resp.content.decode('utf-8', 'replace')
    ok(body.count('class="month-cell') >= 28,
       '  and every day of the month is drawn',
       body.count('class="month-cell'))
    ok(body.count('class="month-dow"') == 7,
       '  under seven weekday headings',
       body.count('class="month-dow"'))

    # THE BUSY DAY SAYS HOW MANY IT COULD NOT SHOW.
    more = re.findall(r'month-more">\+(\d+) more', body)
    ok(more, 'a day with more than three says "+n more"  [Q1]', more)

try:
    from playwright.sync_api import sync_playwright
    import alv_offline                 # E20 - renders stay offline
except Exception:
    sync_playwright = None

if not django_up or not body:
    pass
elif sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the month is drawn', 'playwright or the Bootstrap fixture is '
                               'absent')
else:
    FIX = '<style>%s</style>' % read(FIXCSS)
    i = body.lower().find('</head>')
    DRESSED = body[:i] + FIX + body[i:] if i > 0 else FIX + body

    MEASURE = """() => {
        const cs = [...document.querySelectorAll('.month-cell')];
        const r = cs.map(c => c.getBoundingClientRect());
        const vis = s => [...document.querySelectorAll(s)]
            .filter(e => getComputedStyle(e).display !== 'none').length;
        return {
            cells: cs.length,
            cols: new Set(r.map(x => Math.round(x.left))).size,
            rows: new Set(r.map(x => Math.round(x.top))).size,
            cellW: r.length ? Math.round(r[8].width) : 0,
            cellH: r.length ? Math.round(r[8].height) : 0,
            chips: vis('.month-chip'),
            dots: vis('.month-dots'),
            wide: document.documentElement.scrollWidth >
                  document.documentElement.clientWidth,
            gridW: Math.round(document.querySelector('.month-grid')
                   .getBoundingClientRect().width)
        };
    }"""

    with sync_playwright() as _pw:
        br = _pw.chromium.launch()
        try:
            for w, where, names in ((1200, 'DESKTOP 1200', True),
                                    (390, 'PHONE 390', False)):
                pg = br.new_page(viewport={'width': w, 'height': 1000})
                pg.set_content(DRESSED, wait_until='domcontentloaded')
                m = pg.evaluate(MEASURE)
                print('')
                print('   %s' % where)

                # THE CHECK MC-4 EXISTS FOR.
                ok(m['cols'] == 7,
                   '  the cells sit in SEVEN columns - the fault MC-4 '
                   'found was thirty-five in one', m)
                ok(m['rows'] in (5, 6),
                   '  and %d rows, which is what a month has' % m['rows'],
                   m)
                ok(m['cells'] >= 28,
                   '  %d cells drawn' % m['cells'], m)
                ok(not m['wide'],
                   '  and the page does not scroll sideways', m)

                if names:
                    ok(m['cellW'] >= 140,
                       '  a cell is %dpx - it was 113px with the mini '
                       'calendar beside it, which is fifteen characters'
                       % m['cellW'], m['cellW'])
                    ok(m['chips'] > 0 and m['dots'] == 0,
                       '  names are drawn and marks are not', m)
                else:
                    ok(m['cellW'] <= 60,
                       '  a cell is %dpx, which is about five '
                       'characters' % m['cellW'], m['cellW'])
                    ok(m['chips'] == 0 and m['dots'] > 0,
                       '  so the marks are drawn and the names are not '
                       '- five characters is noise, not a name', m)
                pg.close()
        finally:
            br.close()


# ==========================================================================
head('4. WIDE - the component is gone from the whole tree')
# ==========================================================================
# A SELECTOR THAT MATCHES NOTHING IS A CLAIM THAT HAS STOPPED BEING
# TRUE. This round tripped over one an hour before it was written -
# PF-2's `.picker-filter .alv-seg`, left behind when the strip it
# styled was replaced - so it asks the question of every page rather
# than only of its own.
stray = []
for p in T.templates(include_base=True):
    code = T.code_only(read(p))
    hit = [g for g in OURS if g in code]
    if hit:
        stray.append((T.rel(p), hit))
ok(not stray,
   'no page in either root names a class this component OWNED - '
   '%s' % ', '.join(OURS),
   '; '.join('%s -> %s' % (a, ','.join(b)) for a, b in stray[:6]))

# AND THE SHARED ONES ARE STILL IN USE ELSEWHERE, which is why they
# are not on that list. If this ever comes back empty, `legend-item`
# really has become dead and belongs in a round of its own.
shared = [T.rel(p) for p in T.templates(include_base=True)
          if 'legend-item' in T.code_only(read(p))]
ok(len(shared) >= 3,
   '  while legend-item is still used by %d other page(s) - a class '
   'this page happened to use is not a class it owned'
   % len(shared), shared[:6])
ok('meal_planner.html' not in shared,
   '  and the planner is no longer one of them')

pyhit = []
for dp, dn, fn in os.walk(os.path.join(ROOT, 'pages')):
    dn[:] = [d for d in dn if d not in ('__pycache__', 'migrations')]
    for f in fn:
        if not f.endswith('.py') or '.bak_' in f:
            continue
        p = os.path.join(dp, f)
        if 'calendar_weeks' in T.python_code_only(read(p), payloads=True):
            pyhit.append(os.path.relpath(p, ROOT))
ok(not pyhit, '  and no view still builds calendar_weeks', pyhit)


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
touched = sorted(
    os.path.relpath(os.path.join(dp, f), ROOT)[:-len(SUFFIX)]
    for dp, dn, fn in os.walk(ROOT)
    for f in fn if f.endswith(SUFFIX))
allowed = {'Push-PendingChanges.ps1', 'alv_tree.py', 'alv_rounds.py',
           'test_waiting_down.py',
           os.path.join('pages', 'templates', 'meal_planner.html'),
           os.path.join('pages', 'views', 'recipes', 'meal_planning.py'),
           # TWO TREE-WIDE RE-PINS and one retirement. EXPECT_PAIRS
           # 700 -> 702 for the month grid's two house pairs;
           # IMP_TREE 804 -> 803 DOWNWARD, because the mini calendar's
           # phone block carried the !important this round deletes.
           'test_pair_contrast.py', 'test_important_base.py',
           # AND MC-4'S SUITE, which this round retires and removes
           # from disk - its backup is what makes that reversible.
           'test_mini_grid.py',
           # MN-1'S ONE CLAIM ABOUT THE STRIP, repointed. It asserted
           # the mini calendar marked the selected week's row; the row
           # is gone and the FACT is not, so it now asks the month
           # grid, which tints all seven of that week's cells.
           'test_planner.py'}
ok(len(touched) == 10,
   'ten backups on disk, counted and not typed', '%r' % (touched,))
ok(not set(touched) - allowed,
   '  and every one is a file this round was allowed',
   'unexpected: %s' % ', '.join(sorted(set(touched) - allowed)))

import alv_rounds                                          # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'alv_rounds knows the round')
ok(ME in T.CONVERTED, 'alv_tree knows this suite')
gate = read(GATE)
ok("'%s'" % ME in gate, 'the gate runs this suite')
ok('class="month-grid"' in gate and 'THE MINI CALENDAR WAS HERE' in gate
   and 'THREE SHOWN, THE REST COUNTED' in gate,
   'all three sentinels are pinned in the gate')

# MC-4 IS RETIRED, AND SAID TO BE. It rendered the mini calendar;
# this round deleted it. A suite retires with the thing it judged -
# MN-1 retired two the same way on 18 October - and its lesson did
# not retire with it: the three MC-4 citations in section 1 above are
# where it went.
ok("'test_mini_grid.py'" not in gate,
   'MC-4\'s suite is no longer registered in the gate')
ok('test_mini_grid.py' in gate,
   '  but the gate still SAYS where it went - a suite that vanishes '
   'without a note is one the next reader thinks was never there')
ok("'test_mini_grid.py'" not in read(os.path.join(ROOT, 'alv_tree.py')),
   '  and it is out of alv_tree.CONVERTED')
ok('test_mini_grid.py' not in T.CONVERTED,
   '  as the module itself agrees')
ok('counts COLUMNS' in read(os.path.join(ROOT, ME))
   or 'SEVEN columns' in read(os.path.join(ROOT, ME)),
   '  and this suite is the one that counts columns now')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m and int(m.group(1)) == len(T.CONVERTED),
   'test_waiting_down agrees with alv_tree.CONVERTED - %s against %d'
   % (m.group(1) if m else '?', len(T.CONVERTED)))


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THE MONTH IS THE VIEW, AND THE STRIP IS GONE. It went on a')
print('  measurement and not a preference: a seven-column cell is')
print('  113px with that 320px sidebar and 162px without - fifteen')
print('  characters against twenty-three. A cell cannot carry a')
print('  recipe name while it is there.')
print('')
print('  THIS SUITE COUNTS COLUMNS IN A BROWSER. MC-4 is the round')
print('  where every class name on the old mini calendar was correct')
print('  and the thing drew thirty-five cells in one column, on the')
print('  live site, for four weeks. Two checks read its markup and')
print('  passed every day it was broken.')
print('')
print('  AND FIVE CHARACTERS IS NOT A NAME. Below 768px the names go')
print("  and marks arrive, in the chips' own three colours, which is")
print('  his answer: all three views everywhere, and the phone gets')
print('  dots.')
print('=' * 74)
sys.exit(1 if failed else 0)
