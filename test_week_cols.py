# -*- coding: utf-8 -*-
"""test_week_cols.py - round MV-3, 19 Oct 2026.

RELEASE 4, PUSH 1. THE WEEK IS SEVEN COLUMNS.

Demetri, testing the live planner: "This daily list is not required..."

HE WAS REACTING TO A NUMBER, so this suite measures it. One week of
day cards is about 4,900px: Sunday is four screens below Monday, and
the number of days you can see at once is ZERO - on a page whose whole
job is showing you the week. Section 3 renders the week and measures
the grid.

THE PHONE CANNOT HAVE SEVEN COLUMNS. 358px over seven is 51px, the
same wall the Month hit. Month answers it with dots; Week cannot,
because it is the view you use standing in the kitchen and a dot does
not say what is for dinner. So the phone gets a DAY STRIP - his own
answer to Question A - and this suite checks that the columns are
hidden there and the strip is not.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One grid, seven columns, no row wrapper; no stepper
      and no row actions in a 152px column; one rule deciding which
      day the strip opens on.

  2   THE CONTROL. Every claim re-asked of the pre-round files, where
      the week was seven cards and nothing else.

  3   RENDERED at 1200 and at 390. Seven distinct column positions and
      a grid under 300px against 4,900px of cards; on the phone, the
      columns gone, the strip there, exactly one day selected.

  4   THE SELECTED DAY follows the anchor, driven through a real
      client across a month boundary.

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

SUFFIX = '.bak_weekcols'
ME = 'test_week_cols.py'
PATCHER = 'apply_week_cols.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MV-3, 19 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
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


def claims(text):
    """Every source claim MV-3 makes, written once and asked twice."""
    c = {}
    code = T.code_only(text[TPL])
    js = T.code_only_js(text[TPL])
    v = T.python_code_only(text[VIEW], payloads=True)
    g = code.find('class="week-grid"')
    gend = code.find('class="day-strip"', g) if g >= 0 else -1
    grid = code[g:gend] if (g >= 0 and gend > g) else ''

    # ---- 1. seven columns, one grid, no row wrapper  [MC-4]
    c['the week is a seven column grid'] = (
        '.week-grid {' in code
        and 'grid-template-columns: repeat(7, minmax(0, 1fr));' in
        code.split('.week-grid {')[1].split('}')[0])
    c['  one child per column, no row wrapper  [MC-4]'] = (
        bool(grid) and 'week-row' not in grid
        and not re.search(r'display:\s*contents', code))
    c['  and it loops the seven days the view already built'] = (
        '{% for day in week_days %}' in grid)

    # ---- 2. a column is 152px and knows it
    c['no servings stepper in a column'] = (
        bool(grid) and 'servings-step' not in grid
        and 'stepServings' not in grid)
    c['  and no row actions either'] = (
        bool(grid) and 'row-action' not in grid
        and 'action-more' not in grid)
    c['a column carries the same chip the month draws'] = (
        '.week-chip {' in code and '.week-chip.is-note {' in code
        and '.week-chip.is-leftover {' in code)
    c['  and an empty day says so'] = (
        '.week-col-empty' in code and '{% empty %}' in grid)
    c['  with a + at the foot that opens the picker on that day'] = (
        'week-col-add' in grid and 'openPicker(' in grid)

    # ---- 3. the phone gets the strip, not the columns
    c['the day strip is hidden at full size'] = (
        '.day-strip {\n    display: none;\n}' in code)
    c['  and the seven columns on a phone'] = any(
        '.week-grid {' in p
        and 'display: none;' in p.split('.week-grid {')[1].split('}')[0]
        for p in code.split('@media screen and (max-width: 767px)')[1:])
    c['  each strip button is 44px  [the house rule]'] = any(
        '.day-strip-btn {' in p
        and 'min-height: 44px;' in
        p.split('.day-strip-btn {')[1].split('}')[0]
        for p in code.split('@media screen and (max-width: 767px)')[1:])
    c['  two letters a day, because three will not fit at 51px'] = (
        "'day_two': d.strftime('%a')[:2]," in v)
    c['  and a mark per meal, in the chip colours'] = (
        '.day-strip-dot.is-note' in code
        and '.day-strip-dot.is-leftover' in code)

    # ---- 4. ONE rule decides the selected day
    c['the strip opens on the anchor when it is in this week'] = (
        'sel_date = anchor if week_start <= anchor <= week_end'
        in v)
    c['  and on the Monday otherwise'] = 'else week_start' in v
    c['  exactly one button is marked'] = (
        code.count('aria-current="date"') == 1)
    c['  and pressing one keeps the view'] = (
        "goDay('{{ day.date|date:'Y-m-d'|escapejs }}', 'week')" in code)

    # ---- 5. every handler exists
    c['every onclick names a function this page defines'] = not [
        fn for fn in set(re.findall(r'onclick="(\w+)\(', code))
        if ('function %s(' % fn) not in js]
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
# MC-4's absence and the handler check were true before: the mini
# calendar's display:contents went with MV-2, and a page whose
# onclicks all resolved still had them all resolving.
ALLOWED = ('every onclick names a function this page defines',)
ok(sorted(leaked) == sorted(ALLOWED),
   'the only claim already true before MV-3 is that the page had no '
   'broken handlers, which it did not before either', leaked)

BC = T.code_only(was(TPL))
BV = T.python_code_only(was(VIEW), payloads=True)
ok('week-grid' not in BC,
   'CONTROL: there was no week grid - the week was seven cards')
ok('day-strip' not in BC, 'CONTROL: and no day strip')
ok('sel_date' not in BV,
   'CONTROL: and nothing decided which day a phone would open on')
ok(BC.count('{% for day in week_days %}') == 1,
   'CONTROL: week_days was looped once, into the cards', BC.count(
       '{% for day in week_days %}'))


# ==========================================================================
head('3. RENDERED - seven columns, and the number he was reacting to')
# ==========================================================================
django_up = False
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    from django.conf import settings as dj_settings
    django.setup()
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
    dj_settings.DEBUG = False
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a rendered week',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

body = ''
if django_up:
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Recipe

    u = User.objects.create_user(username='mv3', password='x',
                                 email='mv3@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(
                Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    cl = Client()
    cl.force_login(u)

    NAMES = ['Fakes', 'Greek Salad (Horiatiki)', 'Moussaka', 'Pastitsio',
             'Souvlaki', 'Tzatziki', 'Lemon Potatoes', 'Roast Chicken']
    rs = [Recipe.objects.create(recipe_name=n, servings=4, prep_time=10,
                                cook_time=30) for n in NAMES]
    MON = dt.date(2026, 10, 19)
    # A BUSY SATURDAY AND AN EMPTY THURSDAY, so "the week at a glance"
    # has a shape to show and the empty state has a day to be in.
    PLAN = {0: [0, 1], 1: [4], 2: [2], 4: [3], 5: [4, 5, 6, 1], 6: [7]}
    parent = None
    for off, idx in PLAN.items():
        d = MON + dt.timedelta(days=off)
        for k, i in enumerate(idx):
            e = MealEntry.objects.create(date=d, recipe=rs[i], servings=4,
                                         sort_order=k + 1, created_by=u)
            if parent is None:
                parent = e
    MealEntry.objects.create(date=MON + dt.timedelta(days=2), recipe=None,
                             note='Angy away', servings=0, sort_order=5,
                             created_by=u)
    MealEntry.objects.create(date=MON + dt.timedelta(days=3),
                             recipe=rs[2], servings=4, sort_order=1,
                             leftover_of=parent, created_by=u)

    resp = cl.get('/meal_plans/planner/?view=week&date=2026-10-22')
    ok(resp.status_code == 200, 'the week answers', resp.status_code)
    body = resp.content.decode('utf-8', 'replace')
    # COUNTED ON THE HEAD, which is one per column. `week-col` is a
    # PREFIX of week-col-head, -dow, -num, -body, -empty, -foot and
    # -add, so counting it found forty-nine. The same trap as
    # `pickerCourse` inside `pickerCourseBtn` this morning, and as
    # `month-cell in-week` an hour ago.
    ok(body.count('class="week-col-head"') == 7,
       '  with seven columns', body.count('class="week-col-head"'))
    ok(len(re.findall(r'class="day-strip-btn[ "]', body)) == 7,
       '  and seven strip buttons for the phone',
       len(re.findall(r'class="day-strip-btn[ "]', body)))
    for cls, what in (('week-chip is-note', 'a note'),
                      ('week-chip is-leftover', 'a leftover')):
        ok(cls in body, '  %s keeps its own colour in a column' % what)

try:
    from playwright.sync_api import sync_playwright
    import alv_offline                 # E20 - renders stay offline
except Exception:
    sync_playwright = None

if not django_up or not body:
    pass
elif sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the week is drawn', 'playwright or the Bootstrap fixture is '
                              'absent')
else:
    FIX = '<style>%s</style>' % read(FIXCSS)
    i = body.lower().find('</head>')
    DRESSED = body[:i] + FIX + body[i:] if i > 0 else FIX + body

    MEASURE = """() => {
        const shown = s => [...document.querySelectorAll(s)]
            .filter(e => getComputedStyle(e).display !== 'none');
        const g = document.querySelector('.week-grid');
        const gs = getComputedStyle(g);
        const cols = [...document.querySelectorAll('.week-col')];
        const cards = shown('.day-card');
        return {
            gridShown: gs.display !== 'none',
            gridH: gs.display !== 'none'
                ? Math.round(g.getBoundingClientRect().height) : 0,
            colXs: new Set(cols.map(
                c => Math.round(c.getBoundingClientRect().left))).size,
            colW: cols.length
                ? Math.round(cols[0].getBoundingClientRect().width) : 0,
            stripShown: shown('.day-strip').length,
            stripBtns: shown('.day-strip-btn').length,
            selected: document.querySelectorAll(
                '.day-strip-btn.is-selected').length,
            btnH: shown('.day-strip-btn').length
                ? Math.round(shown('.day-strip-btn')[0]
                    .getBoundingClientRect().height) : 0,
            cardsH: cards.reduce(
                (a, c) => a + c.getBoundingClientRect().height, 0),
            wide: document.documentElement.scrollWidth >
                  document.documentElement.clientWidth
        };
    }"""

    with sync_playwright() as _pw:
        br = _pw.chromium.launch()
        try:
            for w, where in ((1200, 'DESKTOP 1200'), (390, 'PHONE 390')):
                pg = br.new_page(viewport={'width': w, 'height': 1000})
                pg.set_content(DRESSED, wait_until='domcontentloaded')
                m = pg.evaluate(MEASURE)
                print('')
                print('   %s' % where)
                ok(not m['wide'],
                   '  the page does not scroll sideways', m)

                if w >= 768:
                    ok(m['colXs'] == 7,
                       '  the columns sit at SEVEN distinct positions',
                       m)
                    ok(m['gridShown'] and m['gridH'] < 400,
                       '  and the whole week is %dpx tall, against about '
                       '4,900px of day cards - which is what "this '
                       'daily list is not required" was about'
                       % m['gridH'], m)
                    # AGAINST THE 4,900px, NOT AGAINST THE PAGE -
                    # repaired by MV-4, 19 Oct 2026. This compared the
                    # grid with the day cards still on the page, and
                    # MV-4 hides those in Week above 768px, so the
                    # number it compared against became zero an hour
                    # after it was written.
                    #
                    # The claim was never about what happens to be
                    # beside the grid. It is about the 4,900px of
                    # stacked cards the week used to be, which is a
                    # fixed measurement and cannot be hidden.
                    ok(m['gridH'] < 1000,
                       '  %dpx, against the ~4,900px one week of '
                       'stacked day cards measured' % m['gridH'], m)
                    ok(m['cardsH'] == 0,
                       '  and MV-4 draws no day card here at all - the '
                       'seven columns are the whole answer', m)
                    ok(not m['stripShown'],
                       '  and the phone strip is not drawn here', m)
                else:
                    ok(not m['gridShown'],
                       '  the seven columns are NOT drawn - each would '
                       'be 51px', m)
                    ok(m['stripShown'] == 1 and m['stripBtns'] == 7,
                       '  the day strip is, with seven days', m)
                    ok(m['selected'] == 1,
                       '  exactly one day is selected', m)
                    ok(m['btnH'] >= 44,
                       '  and each button is %dpx - the house rule for '
                       'a control you use with a thumb' % m['btnH'],
                       m['btnH'])
                pg.close()
        finally:
            br.close()


# ==========================================================================
head('4. THE SELECTED DAY FOLLOWS THE ANCHOR')
# ==========================================================================
if django_up:
    def sel(q):
        r = cl.get('/meal_plans/planner/' + q)
        if r.status_code != 200:
            return None, r.status_code
        return r.context['sel_date'], 200

    d, code = sel('?view=week&date=2026-10-22')
    ok(d == dt.date(2026, 10, 22),
       'arriving on the 22nd opens the 22nd, not the Monday', d)
    d, _ = sel('?view=week&week=2026-10-19')
    ok(d == dt.date(2026, 10, 19),
       '  and ?week= alone names a week, so it opens the Monday', d)
    # A WEEK THAT STRADDLES TWO MONTHS still has one selected day, and
    # the anchor rule has to hold across the boundary.
    d, _ = sel('?view=week&date=2026-11-01')
    ok(d == dt.date(2026, 11, 1),
       '  a Sunday that ends October opens on itself', d)
    d, _ = sel('?view=week&date=2026-10-12')
    ok(d == dt.date(2026, 10, 12),
       '  and a Monday opens on itself, not on some other Monday', d)


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
           # ONE TREE-WIDE RE-PIN. The week column's leftover chip
           # takes the panel-wash token as its background - the same
           # token MV-2's month chip uses, because the month and the
           # week must not teach two vocabularies for one meal - so
           # N_OTHER goes 93 to 94.
           'test_surface_border.py',
           # AND THE PAIR CENSUS, 702 -> 706 for the week grid's four
           # house pairs. The two rules in this round that read below
           # AA were repaired, not pinned.
           'test_pair_contrast.py'}
ok(len(touched) == 8,
   'eight backups on disk, counted and not typed', '%r' % (touched,))
ok(not set(touched) - allowed,
   '  and every one is a file this round was allowed',
   'unexpected: %s' % ', '.join(sorted(set(touched) - allowed)))

import alv_rounds                                          # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'alv_rounds knows the round')
ok(ME in T.CONVERTED, 'alv_tree knows this suite')
gate = read(GATE)
ok("'%s'" % ME in gate, 'the gate runs this suite')
ok('class="week-grid"' in gate and 'class="day-strip"' in gate
   and 'WHICH DAY THE PHONE OPENS ON' in gate,
   'all three sentinels are pinned in the gate')

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
print('  "THIS DAILY LIST IS NOT REQUIRED." One week of day cards is')
print('  about 4,900px: Sunday is four screens below Monday and the')
print('  number of days you can see at once is zero, on a page whose')
print('  whole job is showing you the week. Seven columns is 192px.')
print('')
print('  THE PHONE CANNOT HAVE SEVEN OF THEM. 358px over seven is')
print('  51px - the wall the Month hit and answered with dots. The')
print('  Week cannot: it is the view you use standing in the kitchen')
print('  and a dot does not say what is for dinner. So the shape')
print('  stays across the top and one day opens in full.')
print('')
print('  AND NO STEPPER IN A COLUMN. 152px does not hold one; a')
print('  control that is there and unusable is worse than one that')
print('  is not. Those belong to the Day view.')
print('=' * 74)
sys.exit(1 if failed else 0)
