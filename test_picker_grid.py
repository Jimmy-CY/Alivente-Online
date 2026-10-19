# -*- coding: utf-8 -*-
"""test_picker_grid.py - round PK-1, 19 Oct 2026.

RELEASE 3, PUSH 2. THE PICKER IS A GRID.

Demetri, on the Add-a-Meal picker on the live site:

    "There is no search or filtering.... also there is so much wasted
     space on the right of each recipe. Should it not be a grid?"
    "Also, I am not able to select a recipe"

FOUR COMPLAINTS, ONE ROOT. `.recipe-option` has never had a CSS rule -
not on this page, not in base.html, not in any of twenty-seven backups
of this template or the calendar it descends from. An image and a block
of text with nothing laying them out, in a container with nothing
laying IT out, and a `.selected` class that pickRecipe() has added
since the picker was written with nothing anywhere drawing it.

He could select a recipe. Nothing told him he had.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. An auto-fill grid, a base .alv-seg filter strip, a
      count, an empty state, and the course ids on every card.

  2   THE CONTROL, asked of .bak_pickergrid, where every claim must
      FAIL.

  3   THE BEHAVIOUR, DRIVEN IN A BROWSER. This is the register that
      matters for a dialog: the filter narrows, the search narrows,
      the two COMPOSE rather than replace each other, a filter that
      matches nothing says so, and clicking a card visibly selects it.

  4   ONE QUERY. Every card prints the courses it belongs to, which is
      a query per card without a prefetch - and this tree has two
      hundred recipes. [E29]

  5   RENDERED, at 1200 and at 390. Three columns and one, no sideways
      scroll, and the dialog shorter than the column it replaced.

  6   Scope, registration and the gate.

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

SUFFIX = '.bak_pickergrid'
ME = 'test_picker_grid.py'
PATCHER = 'apply_picker_grid.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PK-1, 19 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
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
    """Every source claim PK-1 makes, written once and asked twice."""
    c = {}
    code = T.code_only(text[TPL])
    js = T.code_only_js(text[TPL])
    v = T.python_code_only(text[VIEW])
    body = re.split(r'\n(?=function )',
                    js.split('function filterPicker()')[-1])[0]

    # ---- 1. the grid
    c['the picker list is a grid'] = '#pickerList {\n    display: grid;' in code
    c['  auto-fill, so the DIALOG decides the column count'] = (
        'repeat(auto-fill, minmax(240px, 1fr))' in code)
    c['  with a gap instead of a margin per card'] = (
        '#pickerList {' in code and 'gap: 8px;' in
        code.split('#pickerList {')[1].split('}')[0])
    c['  and the card has no bottom margin left'] = (
        '.recipe-option {' in code
        and 'margin-bottom' not in
        code.split('.recipe-option {')[1].split('}')[0])

    # ---- 2. the filter, and it is BASE'S component
    c['there is a course filter'] = 'picker-filter' in code
    c['  built from base\'s .alv-seg'] = (
        'class="alv-seg" role="group"' in code)
    # PAIRED WITH THE STRIP. A page that has no filter at all writes no
    # .alv-seg rule either, so the absence on its own was true before
    # this round and the control section said so.
    c['  and the page writes no .alv-seg rule of its own'] = (
        'class="alv-seg" role="group"' in code
        and not re.search(r'(?m)^\s*\.alv-seg\s*\{', code))
    c['  one button per course, out of the context'] = (
        '{% for course in all_courses %}' in code)
    c['  and an All button that is pressed to begin with'] = (
        'data-course="" aria-pressed="true"' in code)

    # ---- 3. the two narrowings COMPOSE
    c['the filter and the search compose'] = (
        'byName && byCourse' in body)
    c['  the typed text still narrows'] = 'byName' in body
    c['  the chosen course narrows too'] = 'byCourse' in body
    c['  matched on ids, padded on BOTH sides'] = (
        "' ' + pickerCourse + ' '" in body)
    c['  so course 1 cannot match course 11'] = (
        "' ' + (o.dataset.recipeCourses || '') + ' '" in body)

    # ---- 4. the count and the empty state
    c['the dialog says how many of how many'] = 'id="pickerCount"' in code
    c['  and names a plain total when nothing is filtered'] = (
        "shown === total" in body)
    c['a filter that matches nothing says so'] = 'id="pickerEmpty"' in code
    c['  rather than looking like a broken dialog'] = (
        'empty.hidden = shown !== 0' in body)

    # ---- 5. every card knows its courses
    c['each card carries its course ids'] = (
        'data-recipe-courses=' in code)
    c['  from a prefetch, not a query per card  [E29]'] = (
        "prefetch_related('courses')" in v)
    c['  and the context hands the strip its courses'] = (
        "'all_courses':" in v)

    # ---- 6. C19, now that there is a second thing to forget
    c['the filter is reset when the dialog opens  [C19]'] = (
        "pickerCourse = '';" in js.split('function openPicker')[-1]
        .split('\nfunction ')[0])
    c['  and the All button pressed again with it'] = (
        "b.dataset.course ? 'false' : 'true'" in js)

    # ---- 7. MW-1's card is untouched - this round changed the LIST
    c['MW-1\'s selected state is still there'] = (
        '.recipe-option.selected {' in code
        and 'box-shadow: 0 0 0 2px var(--alv-accent-ring);' in code)
    c['  and the row inside a card is still a flex row'] = (
        '.recipe-option {' in code
        and 'display: flex;' in
        code.split('.recipe-option {')[1].split('}')[0])
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
# MW-1's two card claims were true before PK-1 and must be: this round
# changed the LIST, and a round that broke MW-1's card while widening
# its container would be caught by them failing in section 1.
MW1 = ("MW-1's selected state is still there",
       '  and the row inside a card is still a flex row')
ok(sorted(leaked) == sorted(MW1),
   'the only claims already true before PK-1 are MW-1\'s two, which '
   'this round deliberately leaves alone', leaked)


# ==========================================================================
head('3. THE DIALOG, DRIVEN - and 4. ONE QUERY')
# ==========================================================================
# "THE SOURCE SAYS byName && byCourse" IS A CLAIM ABOUT TEXT. "Pressing
# Dessert leaves one of six, and typing over it still leaves that one"
# is a claim about the dialog, and it is the only one that answers what
# he reported.
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
    dj_settings.ALLOWED_HOSTS = list(dj_settings.ALLOWED_HOSTS) + ['testserver']
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
    skip('everything that needs a rendered dialog',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if not django_up:
    pass
elif sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the dialog is driven',
         'playwright or the Bootstrap fixture is absent')
else:
    import datetime as _dt
    from django.contrib.auth.models import Permission, User
    from django.db import connection, reset_queries
    from django.test import Client
    from pages.models import Recipe, RecipeCourse

    u = User.objects.create_user(username='pk1', password='x',
                                 email='pk1@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        u.user_permissions.add(Permission.objects.get(codename=codename))
    cl = Client()
    cl.force_login(u)

    COURSES = ['Starter', 'Main', 'Dessert', 'Snack']
    cs = [RecipeCourse.objects.create(name=n, display_order=i)
          for i, n in enumerate(COURSES)]
    # SIX RECIPES ROUND FOUR COURSES, so Dessert holds exactly one and
    # the string 'ba' matches exactly that one - which is what makes
    # "the two compose" a measurable claim rather than a hopeful one.
    NAMES = ['Avgolemono', 'Beef Stifado', 'Baklava', 'Dolmades',
             'Briam', 'Galaktoboureko']
    for i, n in enumerate(NAMES):
        r = Recipe.objects.create(recipe_name=n, servings=6)
        r.courses.add(cs[i % 4])
    DESSERT = cs[2]
    MON = _dt.date(2026, 10, 19)
    URL = '/meal_plans/planner/?week=' + MON.strftime('%Y-%m-%d')

    # ---- 4. ONE QUERY, measured before anything is rendered.
    reset_queries()
    resp = cl.get(URL)
    few = len(connection.queries)
    ok(resp.status_code == 200, 'the planner answers', resp.status_code)
    for i in range(24):
        r = Recipe.objects.create(recipe_name='Filler %02d' % i, servings=4)
        r.courses.add(cs[i % 4])
    reset_queries()
    resp = cl.get(URL)
    many = len(connection.queries)
    ok(many <= few,
       'thirty recipes cost %d queries against six recipes\' %d - the '
       'courses come from a prefetch, not one query per card  [E29]'
       % (many, few), (few, many))
    body = resp.content.decode('utf-8', 'replace')
    ok(body.count('class="recipe-option"') == 30,
       '  and all thirty cards are drawn',
       body.count('class="recipe-option"'))
    ok(body.count('data-course=') == len(COURSES) + 1,
       '  with %d course buttons - one per course, plus All'
       % (len(COURSES) + 1), body.count('data-course='))

    FIX = '<style>%s</style>' % read(FIXCSS)
    i = body.lower().find('</head>')
    DRESSED = body[:i] + FIX + body[i:] if i > 0 else FIX + body

    OPEN = """() => {
        const d = document.getElementById('pickerModal');
        const css = [...document.querySelectorAll('style')];
        d.classList.add('show');
        d.style.display = 'block';
        d.style.position = 'static';
        document.body.innerHTML = '';
        css.forEach(s => document.body.appendChild(s));
        document.body.appendChild(d);
        filterPicker();
    }"""
    STATE = """() => ({
        count: document.getElementById('pickerCount').textContent,
        shown: [...document.querySelectorAll('.recipe-option')]
                 .filter(o => o.style.display !== 'none')
                 .map(o => o.dataset.recipeName),
        empty: !document.getElementById('pickerEmpty').hidden,
        pressed: [...document.querySelectorAll('.picker-filter button')]
                   .filter(b => b.getAttribute('aria-pressed') === 'true')
                   .map(b => b.textContent.trim())
    })"""

    with sync_playwright() as _pw:
        # PLAIN launch(). A suite that names a path only one machine has
        # is a suite that only runs on one machine.
        _br = _pw.chromium.launch()
        pg = _br.new_page(viewport={'width': 1200, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content(DRESSED, wait_until='domcontentloaded')
        pg.evaluate(OPEN)

        s = pg.evaluate(STATE)
        ok(len(s['shown']) == 30, 'the dialog opens showing all thirty',
           len(s['shown']))
        ok(s['count'] == '30 recipes',
           '  and says so in words, not as a fraction', s['count'])
        ok(s['pressed'] == ['All'], '  with All pressed', s['pressed'])
        ok(not s['empty'], '  and no empty state')

        # ---- THE FILTER NARROWS
        pg.evaluate("""(id) => {
            const b = [...document.querySelectorAll('.picker-filter button')]
                        .find(x => x.dataset.course === String(id));
            pickCourse(b);
        }""", DESSERT.recipe_course_id)
        s = pg.evaluate(STATE)
        ok(s['pressed'] == ['Dessert'],
           'pressing Dessert presses only Dessert', s['pressed'])
        ok('baklava' in s['shown'],
           '  and Baklava is showing', s['shown'])
        ok(all('avgolemono' != n for n in s['shown']),
           '  while Avgolemono, a Starter, is not', s['shown'])
        ok(s['count'].endswith(' of 30'),
           '  and the count reads as a fraction now - %s' % s['count'],
           s['count'])
        n_dessert = len(s['shown'])

        # ---- AND THE SEARCH COMPOSES WITH IT, which is the claim
        pg.evaluate("""() => {
            document.getElementById('pickerSearch').value = 'ba';
            filterPicker();
        }""")
        s = pg.evaluate(STATE)
        ok(s['shown'] == ['baklava'],
           'typing "ba" ON TOP of Dessert leaves Baklava alone - the two '
           'COMPOSE, neither replaces the other', s['shown'])
        ok(s['pressed'] == ['Dessert'],
           '  and Dessert is still pressed - typing did not clear it',
           s['pressed'])

        # ---- EITHER ALONE STILL WORKS
        pg.evaluate("""() => {
            const b = [...document.querySelectorAll('.picker-filter button')]
                        .find(x => !x.dataset.course);
            pickCourse(b);
        }""")
        s = pg.evaluate(STATE)
        ok(s['shown'] == ['baklava'],
           'clearing the course leaves the search doing the work',
           s['shown'])
        pg.evaluate("""() => {
            document.getElementById('pickerSearch').value = '';
            filterPicker();
        }""")
        s = pg.evaluate(STATE)
        ok(len(s['shown']) == 30, '  and clearing both shows all thirty',
           len(s['shown']))

        # ---- A FILTER THAT MATCHES NOTHING SAYS SO
        pg.evaluate("""() => {
            document.getElementById('pickerSearch').value = 'zzzzz';
            filterPicker();
        }""")
        s = pg.evaluate(STATE)
        ok(s['shown'] == [], 'a search that matches nothing hides every card')
        ok(s['empty'],
           '  AND THE DIALOG SAYS SO - an empty grid with no message is '
           'a dialog that looks broken')
        ok(s['count'] == '0 of 30', '  with the count at zero', s['count'])

        # ---- AND THE THING HE ACTUALLY REPORTED
        pg.evaluate("""() => {
            document.getElementById('pickerSearch').value = '';
            filterPicker();
            pickRecipe(document.querySelector('.recipe-option'));
        }""")
        sel = pg.evaluate("""() => {
            const o = document.querySelector('.recipe-option');
            const st = getComputedStyle(o);
            return {cls: o.className, shadow: st.boxShadow,
                    bg: st.backgroundColor, border: st.borderColor,
                    add: !document.getElementById('pickerAdd').disabled};
        }""")
        ok('selected' in sel['cls'],
           'CLICKING A CARD SELECTS IT', sel['cls'])
        ok(sel['add'], '  and arms the Add Meal button', sel['add'])
        # THE WHOLE POINT. He could select; nothing TOLD him he had.
        ok(sel['shadow'] not in ('none', ''),
           '  AND IT IS VISIBLE - a ring, %s' % sel['shadow'],
           sel['shadow'])
        ok(sel['bg'] not in ('rgba(0, 0, 0, 0)', 'transparent'),
           '  and a tint, %s - two signals, not one' % sel['bg'],
           sel['bg'])
        pg.close()

        # ======================================================
        head('5. RENDERED - three columns and one')
        # ======================================================
        VH = 900
        for w, where, want in ((1200, 'desktop', 3), (390, 'phone', 1)):
            pg = _br.new_page(viewport={'width': w, 'height': VH})
            pg.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg.set_content(DRESSED, wait_until='domcontentloaded')
            pg.evaluate(OPEN)
            m = pg.evaluate("""() => {
                const cs = [...document.querySelectorAll('.recipe-option')];
                const xs = new Set(cs.map(
                    c => Math.round(c.getBoundingClientRect().left)));
                const l = document.getElementById('pickerList');
                const add = document.getElementById('pickerAdd');
                return {cols: xs.size, cards: cs.length,
                        addTop: Math.round(
                            add.getBoundingClientRect().top),
                        listH: Math.round(l.getBoundingClientRect().height),
                        over: l.scrollWidth > l.clientWidth + 1,
                        wide: document.documentElement.scrollWidth >
                              document.documentElement.clientWidth};
            }""")
            ok(m['cols'] == want,
               '%-7s the thirty cards sit in %d column(s)' % (where, want),
               m['cols'])
            ok(not m['wide'],
               '  and the dialog does not scroll sideways', m)
            ok(not m['over'],
               '  nor does the list inside it', m)
            # CAPPED, AND THE CONTROLS UNDER IT REACHABLE. The first
            # cut asserted a flat 430px and FOUND A REAL FAULT at 390:
            # MW-1's phone block carried `max-height: none !important`,
            # restored on the reasoning that the override existed to
            # undo a desktop cap - true for a column, wrong for a grid.
            # The phone list measured 2,572px, with the Servings field
            # and the Add Meal button below the fold.
            ok(m['listH'] <= VH // 2 + 2,
               '  the list is capped at %dpx - half the screen or less, '
               'so Add Meal stays reachable' % m['listH'], m['listH'])
            ok(m['addTop'] < VH,
               '  and the Add Meal button is ON the screen at %dpx'
               % m['addTop'], (m['addTop'], VH))
            pg.close()
        _br.close()


# ==========================================================================
head('6. CONTROLS, REGISTRATION AND THE GATE')
# ==========================================================================
from alv_rounds import ROUNDS                                 # noqa: E402

old = T.code_only(was(TPL))
ok('picker-filter' not in old,
   'reverting the planner takes the filter strip out, so section 1 '
   'would FAIL')
ok('display: grid;' not in old.split('#pickerList {')[1].split('}')[0],
   '  and the list is one column again')
ok('max-height: none !important' in old,
   '  with the phone override back, which is what section 5 measured '
   'at 2,572px')
ok("prefetch_related('courses')" not in T.python_code_only(was(VIEW)),
   '  and the view back to a query per card')

# THE INSTRUMENTS. This round's own prose quotes the override it
# deletes and names .alv-seg while forbidding a local copy of it.
ok('max-height: none !important' in read(os.path.join(ROOT, PATCHER)),
   'this round\'s patcher quotes the override it removes')
ok('max-height: none !important' not in T.code_only(NOW[TPL]),
   '  and the page does not carry it any more')
ok(not re.search(r'(?m)^\s*\.alv-seg\s*\{', T.code_only(NOW[TPL])),
   'the page writes no .alv-seg rule')
ok('.alv-seg' in NOW[TPL],
   '  though it names the class twice, which is why that is asked of '
   'the code and not of the file')
ok(re.search(r'(?m)^\s*\.alv-seg\s*\{', T.code_only(read(BASE))) is not None,
   '  and base is where the component really lives')

# THE PAGE STILL HOLDS TOGETHER.
nt = NOW[TPL]
ok(nt.count('<div') == nt.count('</div>'),
   'the planner\'s divs balance - %d and %d'
   % (nt.count('<div'), nt.count('</div>')))
for a, b in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
    ok(nt.count(a) == nt.count(b),
       '  and its %s tags close - %d and %d'
       % (a, nt.count(a), nt.count(b)))
ok(nt.count('/*') == nt.count('*/'),
   '  and the CSS comments balance - %d and %d'
   % (nt.count('/*'), nt.count('*/')))
ok('new bootstrap.Modal' not in T.code_only_js(nt),
   '  and no Bootstrap 5 modal call - base loads 4.1.3  [A4]')

# WIDE FROM BIRTH. The filter strip belongs to one dialog.
pages_all = T.templates(include_base=False)
for text in ('picker-filter', 'function pickCourse('):
    holders = [T.rel(p) for p in pages_all
               if text in T.code_only_js(read(p))]
    ok(holders == ['meal_planner.html'],
       'only the planner carries %r' % text, holders)

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:])
ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_mealweek'),
   '  and after .bak_mealweek, whose card rules it builds on  '
   '[lesson 54]', ROUNDS[-4:])
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is on the push gate' % ME)
for text in ('function pickCourse(', 'id="pickerCount"',
             "prefetch_related('courses')"):
    ok(text in ps1, '  the pre-flight can see %r' % text)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)
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
print('  THE PICKER IS A GRID, AND IT FILTERS. Three columns on a')
print('  desktop and one on a phone, a course strip that composes')
print('  with the search instead of replacing it, and a line that')
print('  says how many of how many are showing.')
print('')
print('  "I AM NOT ABLE TO SELECT A RECIPE" - he could. The click')
print('  landed, the class went on, and nothing in the application')
print('  drew it: .recipe-option has never had a CSS rule, in this')
print('  file or in base or in twenty-seven backups. The only signal')
print('  was a button un-greying at the foot of a list he had')
print('  scrolled past. MW-1 drew the state this morning; this round')
print('  gave the list a shape to draw it in.')
print('')
print('  AND THE SUITE FOUND ONE MORE. The phone block carried')
print('  max-height: none !important, which MW-1 restored on the')
print('  reasoning that it existed to undo a desktop cap. True for a')
print('  column; wrong for a grid. Thirty cards measured 2,572px,')
print('  with Add Meal below the fold.')
print('=' * 74)
sys.exit(1 if failed else 0)
