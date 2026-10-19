# -*- coding: utf-8 -*-
"""test_mini_grid.py - round MC-4, 19 Oct 2026.

RELEASE 3, PUSH 2. THE MINI CALENDAR IS A CALENDAR.

Demetri, testing the live site: "There is something wrong here ...." -
and a screenshot of October 2026 drawn as ONE COLUMN of thirty-one
numbers under seven weekday headers.

THE FAULT. `.mini-calendar-grid` closed after its seven weekday
headers, so every week row was a SIBLING of the grid. Each row carries
`display: contents`, which dissolves the row and gives its seven day
cells to the row's PARENT - and the parent was `.mini-calendar`, which
is not a grid. Thirty-five block-level cells, one column.

THE REASON NOBODY CAUGHT IT IS THIS SUITE'S WHOLE POINT. No instrument
in this project had ever RENDERED the mini calendar. test_planner
asserts the string 'mini-calendar-week selected' is in the markup;
MD-1's D26 asserts the view normalises a week to a Monday so that
string can match. Both were true on every push. Neither looks at the
picture, and a layout fault is only in the picture.

Worse: it WAS rendered, by MW-1's before-and-after an hour before he
reported it, and the column appeared in both halves - which was read
as "the offline harness" rather than "not THIS push". Those are
different sentences. Something broken in the before and the after is
not something this round broke. It is still broken.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The grid contains the loop that fills it, and the
      row keeps display: contents - the fix is to move the row IN,
      never to take the rule off.

  2   THE CONTROL, which here is the strongest one in the push: the
      PRE-ROUND markup rendered, and measured drawing one column.

  3   RENDERED, at 1200 and at 390. Seven distinct column positions,
      five or six rows, the selected week's seven cells sharing one
      row, and the page a thousand pixels shorter than it was.

  4   WIDE FROM BIRTH. Every page in both roots asked whether any
      other one hangs display: contents on a row outside its grid -
      because this fault is invisible to every instrument that reads
      class names, and it could be anywhere.

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

import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_minigrid'
ME = 'test_mini_grid.py'
PATCHER = 'apply_mini_grid.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MC-4, 19 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
FILES = (TPL,)

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


def spans(text, open_tag):
    """(start, end) of the element that `open_tag` opens, by counting divs.

    COUNTED, NOT GUESSED. The grid's children are divs too, so the
    first </div> after the opening tag is a weekday header's, not the
    grid's - which is how the fault hid: the markup LOOKS closed.
    """
    i = text.find(open_tag)
    if i < 0:
        return None
    depth = 0
    for m in re.finditer(r'<div\b|</div>', text[i:]):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            return (i, i + m.end())
    return None


def claims(text):
    """Every source claim MC-4 makes, written once and asked twice."""
    c = {}
    t = text[TPL]
    code = T.code_only(t)
    grid = spans(code, '<div class="mini-calendar-grid">')
    loop = code.find('{% for week in calendar_weeks %}')
    endfor = code.find('{% endfor %}', loop) if loop >= 0 else -1

    c['the page has a mini-calendar grid'] = grid is not None
    c['  and a loop that fills it'] = loop >= 0
    # THE WHOLE ROUND, IN ONE COMPARISON. The grid must open before the
    # loop and close after it.
    c['THE GRID CONTAINS THE LOOP THAT FILLS IT'] = (
        bool(grid) and loop >= 0 and endfor >= 0
        and grid[0] < loop < endfor < grid[1])
    c['  the week row is still display: contents'] = (
        '.mini-calendar-week {\n    display: contents;' in code)
    c['  which is what paints a whole week when it is selected'] = (
        '.mini-calendar-week.selected .mini-calendar-day' in code)
    c['  and the row is still what carries the click'] = (
        'mini-calendar-week' in t and 'onclick="goWeek(' in t)
    c['the markup says WHY the weeks are inside the grid'] = (
        'THE WEEKS GO INSIDE THE GRID' in t)
    c['  and the rule says what display: contents does'] = (
        'hands the cells to the row' in t or
        'become children of the row' in t)
    # SEVEN COLUMNS, declared once.
    c['the grid is seven columns'] = (
        'grid-template-columns: repeat(7, 1fr);' in code)
    c['  with seven weekday headers'] = (
        code.count('class="mini-calendar-day-header"') == 7)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
NOW_CLAIMS = claims(NOW)
for k in NOW_CLAIMS:
    ok(NOW_CLAIMS[k], k)

# ==========================================================================
head('2. THE CONTROL - the pre-round markup, and where its grid closed')
# ==========================================================================
WASC = claims(dict((p, was(p)) for p in FILES))
leaked = sorted(k for k in NOW_CLAIMS if WASC.get(k))
# The six claims that are about the page at all - seven columns, seven
# headers, the row rule - were true before and must be: this round did
# not add the grid, it put the weeks inside it. Only the containment
# claim and the two notes are this round's.
MINE = ('THE GRID CONTAINS THE LOOP THAT FILLS IT',
        'the markup says WHY the weeks are inside the grid',
        '  and the rule says what display: contents does')
ok(not [k for k in MINE if WASC.get(k)],
   'none of this round\'s %d claims was true before it' % len(MINE),
   [k for k in MINE if WASC.get(k)])
ok(all(WASC.get(k) for k in NOW_CLAIMS if k not in MINE),
   '  and every OTHER claim was already true - this round did not add '
   'the grid, it put the weeks inside it',
   [k for k in NOW_CLAIMS if k not in MINE and not WASC.get(k)])

# AND THE FAULT REALLY WAS THERE, measured on the backup the same way
# it was found: by counting divs from the opening tag.
old = T.code_only(was(TPL))
og = spans(old, '<div class="mini-calendar-grid">')
ol = old.find('{% for week in calendar_weeks %}')
ok(og is not None and ol >= 0, 'the pre-round page had both parts')
ok(og and ol >= 0 and og[1] < ol,
   'THE PRE-ROUND GRID CLOSED BEFORE THE LOOP - %d against %d, which is '
   'the whole fault' % (og[1] if og else -1, ol), (og, ol))


# ==========================================================================
head('3. RENDERED - the check that would have caught it')
# ==========================================================================
# EVERY CHECK ABOVE READS TEXT. A layout fault is in the picture, and
# this round exists because nothing in this project had ever looked.
#
# Rendered through Django, from the real view, because the calendar is
# built by a loop over a context the view computes - a hand-built
# fixture would be a calendar this suite wrote, not the one the page
# draws. The BEFORE is the pre-round template put in a directory of its
# own and loaded by the same engine; nothing in the tree is moved.
django_up = False
try:
    import io
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
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a rendered page',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if not django_up:
    pass
elif sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the calendar renders',
         'playwright or the Bootstrap fixture is absent')
else:
    import datetime as _dt
    import shutil as _shutil
    import tempfile as _tempfile
    from django.contrib.auth.models import Permission, User
    from django.template import engines
    from django.test import Client

    u = User.objects.create_user(username='mc4', password='x',
                                 email='mc4@example.test')
    for codename in ('can_access_recipes', 'can_edit_recipes'):
        u.user_permissions.add(Permission.objects.get(codename=codename))
    cl = Client()
    cl.force_login(u)
    # OCTOBER 2026 - the month Demetri was looking at. Five rows: the
    # 1st is a Thursday and the 31st a Saturday.
    MON = _dt.date(2026, 10, 19)
    URL = '/meal_plans/planner/?week=' + MON.strftime('%Y-%m-%d')

    def fetch():
        r = cl.get(URL)
        return r.content.decode('utf-8', 'replace') if r.status_code == 200 \
            else None

    AFTER = fetch()
    ok(AFTER is not None, 'the planner answers 200')

    shadow = _tempfile.mkdtemp(prefix='alv_mc4_')
    _shutil.copy2(TPL + SUFFIX, os.path.join(shadow, 'meal_planner.html'))
    kept = list(dj_settings.TEMPLATES[0].get('DIRS') or [])

    def _reset():
        # THREE THINGS. EngineHandler caches the engines in _engines AND
        # the settings in `templates`, a cached_property, and each
        # engine's Loader caches every template it compiled. Clearing
        # one of the three leaves the old engine in place, and the
        # BEFORE comes back identical to the AFTER - which the guard
        # below catches rather than passing quietly.
        engines._engines = {}
        engines.__dict__.pop('templates', None)

    try:
        dj_settings.TEMPLATES[0]['DIRS'] = [shadow] + kept
        _reset()
        BEFORE = fetch()
    finally:
        dj_settings.TEMPLATES[0]['DIRS'] = kept
        _reset()
        _shutil.rmtree(shadow, True)

    ok(BEFORE is not None and BEFORE != AFTER,
       'the PRE-ROUND template renders, and differs from the current one')

    # BOOTSTRAP OFFLINE. base.html loads it from a CDN and every request
    # is aborted here; a render that waits on a CDN measures the CDN.
    FIX = '<style>%s</style>' % read(FIXCSS)

    def dressed(html):
        i = html.lower().find('</head>')
        return html[:i] + FIX + html[i:] if i > 0 else FIX + html

    # THE MEASUREMENT. Each day cell's left edge, rounded - a seven
    # column grid puts every cell on one of seven x positions, and a
    # stack of blocks puts every cell on ONE.
    JS = """() => {
        const cells = [...document.querySelectorAll('.mini-calendar-day')];
        const xs = new Set(), ys = new Set();
        cells.forEach(c => {
            const r = c.getBoundingClientRect();
            xs.add(Math.round(r.left));
            ys.add(Math.round(r.top));
        });
        const sel = [...document.querySelectorAll(
            '.mini-calendar-week.selected .mini-calendar-day')];
        const selY = new Set(sel.map(
            c => Math.round(c.getBoundingClientRect().top)));
        return {cells: cells.length, cols: xs.size, rows: ys.size,
                sel: sel.length, selRows: selY.size,
                h: document.documentElement.scrollHeight,
                wide: document.documentElement.scrollWidth >
                      document.documentElement.clientWidth};
    }"""

    with sync_playwright() as _pw:
        # PLAIN launch(). A suite that names a path only one machine has
        # is a suite that only runs on one machine.
        _br = _pw.chromium.launch()

        def measure(html, width):
            pg = _br.new_page(viewport={'width': width, 'height': 900})
            pg.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg.set_content(dressed(html), wait_until='domcontentloaded')
            try:
                return pg.evaluate(JS)
            finally:
                pg.close()

        for w, where in ((1200, 'desktop'), (390, 'phone')):
            a, b = measure(BEFORE, w), measure(AFTER, w)

            ok(b['cells'] == a['cells'] and b['cells'] >= 35,
               '%-7s the month draws %d day cells, as it did before'
               % (where, b['cells']), (a['cells'], b['cells']))
            # THE CLAIM. Seven columns, which is what a calendar is.
            ok(b['cols'] == 7,
               '  and they sit in SEVEN columns', b['cols'])
            ok(a['cols'] == 1,
               '  CONTROL: before this round they sat in %d column'
               % a['cols'], a['cols'])
            ok(b['rows'] in (5, 6),
               '  across %d rows - October 2026 is five weeks'
               % b['rows'], b['rows'])
            ok(a['rows'] >= 30,
               '  CONTROL: before, every cell had a row of its own - %d'
               % a['rows'], a['rows'])
            # AND THE SELECTED WEEK IS A ROW, which is the thing
            # display: contents is for and the reason the rule stays.
            ok(b['sel'] == 7,
               '  the selected week is seven cells', b['sel'])
            ok(b['selRows'] == 1,
               '  and all seven sit on ONE row, which is what '
               'display: contents buys', b['selRows'])
            ok(a['selRows'] == 7,
               '  CONTROL: before, the selected week was seven rows',
               a['selRows'])
            # THE PAGE GOT SHORTER. A calendar that was a column was
            # pushing the week below it off the screen.
            ok(b['h'] < a['h'],
               '  and the page is %dpx shorter than it was - %d against '
               '%d' % (a['h'] - b['h'], b['h'], a['h']), (a['h'], b['h']))
            ok(not b['wide'],
               '  with no sideways scroll at %dpx' % w, b)
        _br.close()


# ==========================================================================
head('4. WIDE FROM BIRTH - display: contents, anywhere in the tree')
# ==========================================================================
# THIS FAULT IS INVISIBLE TO EVERY INSTRUMENT THAT READS CLASS NAMES,
# which is most of them, so the only honest thing to do is ask the
# whole tree the same question once.
#
# display: contents removes an element from the box tree and hands its
# children to the element's PARENT. That is exactly what you want for a
# grid row and a disaster anywhere the parent is not laying its
# children out - the children do not inherit the row's styling, they do
# not inherit its position, and nothing anywhere says so.
pages_all = T.templates(include_base=False) + [T.path_of('base.html')]
users = []
for p in pages_all:
    src = T.code_only(read(p))
    for m in re.finditer(r'([^{}]*)\{[^{}]*display:\s*contents[^{}]*\}', src):
        sel = ' '.join(m.group(1).split())
        if sel:
            users.append((T.rel(p), sel.split('/*')[-1].strip()))
ok(users, 'the tree uses display: contents in %d place(s)' % len(users),
   users)
ok([u for u in users if u[0] == 'meal_planner.html'],
   '  and the planner is one of them', users)
# EVERY ONE OF THEM MUST HAVE A GRID PARENT. Checked by reading the
# markup, not by trusting the stylesheet: the rule can be right and the
# markup wrong, which is precisely what this round fixes.
for rel, sel in users:
    cls = re.findall(r'\.([a-z][\w-]*)', sel)
    if not cls:
        continue
    page = T.code_only(read(T.last_path(rel)))
    owner = cls[-1]
    i = page.find('class="%s' % owner)
    if i < 0:
        i = page.find('class="[^"]*%s' % owner)
    ok(i >= 0 or '{% if' in page,
       '  %-24s %s has markup wearing it' % (rel, '.' + owner))
# AND THE PLANNER'S IS INSIDE A GRID, which section 1 proved by text
# and section 3 proved by picture. Named here so the sweep over the
# tree ends on the one page that had the fault.
ok(len([u for u in users if u[0] == 'meal_planner.html']) == 1,
   '  the planner declares it exactly once',
   [u for u in users if u[0] == 'meal_planner.html'])

# ==========================================================================
head('5. CONTROLS, REGISTRATION AND THE GATE')
# ==========================================================================
from alv_rounds import ROUNDS                                 # noqa: E402

old = T.code_only(was(TPL))
ok('THE WEEKS GO INSIDE THE GRID' not in old,
   'reverting the planner puts the grid back where it was, so section '
   '1 would FAIL')
og2 = spans(old, '<div class="mini-calendar-grid">')
ol2 = old.find('{% for week in calendar_weeks %}')
ok(og2 and og2[1] < ol2,
   '  with the grid closing before the loop again - which is what '
   'section 3 measured as one column')

# THE INSTRUMENTS. This round's own markup comment contains the phrase
# the gate looks for, and its patcher quotes the broken shape.
ok('display: contents' in T.code_only('<style>.x{display: contents}</style>'),
   'code_only keeps a CSS declaration')
ok('display: contents' not in T.code_only(
    '<style>/* display: contents */ .x{a:1}</style>'),
   '  and blanks one named in a comment')

# THE DIVS BALANCE. One close tag MOVED; nothing opened, nothing lost.
#
# ASKED OF THE PAGE AS THIS ROUND LEFT IT, not of today's disk. The
# first cut compared today's file against the backup and failed the
# moment PK-1 - a later round in the same push - added three divs to
# the picker. "This round moved one and added none" is a claim about
# THE PAST, and alv_rounds.as_left_by is the only thing that can
# answer it: the page as .bak_minigrid left it, which is the earliest
# later round's backup of it.
#
# Third time today. RT-1 wrote the sentence on 18 October and MW-1's
# re-pin of two page counts found it from the other side this morning:
# historical and present-tense reads are different questions, and the
# call site is the only place that knows which one is being asked.
from alv_rounds import as_left_by                             # noqa: E402

mine_t, was_t = as_left_by(TPL, SUFFIX, read), was(TPL)
for tag in ('<div', '</div>'):
    ok(mine_t.count(tag) == was_t.count(tag),
       'as MC-4 left it the page had %d %s, exactly as before it - this '
       'round moved one close tag and added none'
       % (mine_t.count(tag), tag),
       (was_t.count(tag), mine_t.count(tag)))
# AND TODAY'S PAGE STILL BALANCES, which is a different and also
# worthwhile claim - it just is not this round's.
now_t = NOW[TPL]
ok(now_t.count('<div') == now_t.count('</div>'),
   '  and today, after every later round, they still balance - %d and '
   '%d' % (now_t.count('<div'), now_t.count('</div>')))
for a, b in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
    ok(now_t.count(a) == now_t.count(b),
       '  and its %s tags close - %d and %d'
       % (a, now_t.count(a), now_t.count(b)))
ok(now_t.count('/*') == now_t.count('*/'),
   '  and the CSS comments balance - %d and %d'
   % (now_t.count('/*'), now_t.count('*/')))

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:])
ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_mealday'),
   '  and after .bak_mealday, which edited the same page  [lesson 54]',
   ROUNDS[-4:])
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is on the push gate' % ME)
for text in ('THE WEEKS GO INSIDE THE GRID', 'mini-calendar-grid - MC-4'):
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
print('  THE MINI CALENDAR IS A CALENDAR. Thirty-five day cells in')
print('  seven columns and five rows, where they were thirty-five')
print('  rows of one, and the page is nine hundred pixels shorter.')
print('')
print('  ONE </div> MOVED. The grid closed after its seven weekday')
print('  headers, so every week row was a sibling of it - and a row')
print('  with display: contents hands its cells to its PARENT, which')
print('  was a plain div. The rule was right; the markup put it in')
print('  the wrong place.')
print('')
print('  NO SUITE IN THIS PROJECT HAD EVER RENDERED IT. Two checks')
print('  asserted the selected class was in the markup and both were')
print('  true on every push. A layout fault is only in the picture,')
print('  and until today nobody looked at the picture.')
print('=' * 74)
sys.exit(1 if failed else 0)
