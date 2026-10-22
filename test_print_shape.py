# -*- coding: utf-8 -*-
"""test_print_shape.py - round RG-1, 21 Oct 2026.

THE PRINTED PLAN HAD ONE SHAPE FOR THREE DIFFERENT THINGS.

    "Day view Print, prints a Week view."
    "I don't like the look of the Monthly Print or the weekly ..
     Can't we make this prettier?? Can the Month fit on one A4 page?"

BOTH ARE THE SAME FAULT. PP-1 built one layout - a stack of week
grids with a `Week of 19 Oct` strip above each - and gave every range
to it. A single day became a seven-column grid with six columns
greyed out. It WAS a week. It had one day in it.

AND test_print_plan AGREED WITH IT. Its claim read "A DAY is one week
of grid with one day lit and six dimmed" and it passed every time,
because that is exactly what the page did. An instrument can only
tell you the thing is what you said it was. Demetri looked at the
paper. RG-1 inverts that pin in the same patcher that changes the
page, and section 5 runs the whole of PP-1's suite to prove the two
descriptions have not come apart.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The range chooses the sheet, there are four of
      them, the sheet is one page tall, base's furniture is off the
      paper, and not one colour in the stylesheet is a literal.

  2   THE CONTROL. Re-asked of .bak_printshape, where there was one
      layout and no choice.

  3   ON PAPER. Five ranges printed to real A4 through Chromium -
      a day, a week, a five-week month, a SIX-week month and a
      fortnight across two months. The page count and the paper size
      are read out of the PDF, and every meal is measured against
      the edge of the sheet it is on.

  4   NOTHING TRUNCATES. `Amygdalopita` came out `Amygdalo...` in a
      130px column while this was being drawn. On paper that is a
      name you cannot read.

  5   PP-1's SUITE, RUN. A pin moved in the patcher is a pin that
      has to still fit.

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
import subprocess
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_printshape'
ME = 'test_print_shape.py'
PATCHER = 'apply_print_shape.py'
PS1 = 'Push-PendingChanges.ps1'
PPT = 'test_print_plan.py'
MARK = 'RG-1, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_print.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
PINS = os.path.join(ROOT, PPT)
GATE = os.path.join(ROOT, PS1)
FILES = (TPL, VIEW, PINS)

# A4, IN POSTSCRIPT POINTS, WHICH IS WHAT A PDF MEDIABOX IS IN.
# 595 x 842 portrait, 842 x 595 landscape, give or take a point.
A4 = (595, 842)

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


def fn(src, name):
    """One module-level function's body, or '' if it is not there."""
    m = re.search(r'^def %s\(' % re.escape(name), src, re.M)
    if not m:
        return ''
    rest = src[m.start():]
    nxt = re.search(r'\n(?=(?:def |@)\w)', rest[1:])
    return rest[:nxt.start() + 1] if nxt else rest


def claims(bundle):
    page = T.code_only(bundle[TPL])
    style = page[page.find('<style>'):page.find('</style>')]
    seg = fn(T.python_code_only(bundle[VIEW], payloads=True),
             'meal_plan_print')
    c = {}
    c['THE RANGE CHOOSES THE SHEET - the finding'] = (
        "sheet = 'day'" in seg)
    c['  four of them and no more'] = (
        sorted(set(re.findall(r"sheet = '(\w+)'", seg)))
        == ['day', 'month', 'range', 'week'])
    c['  a week is a Monday and six days after it'] = (
        "start.weekday() == 0 and (end - start).days == 6" in seg)
    c['  a month is the first to the last'] = (
        'start.day == 1 and end == last_of_month' in seg)
    c['  and the day sheet is handed that day meals'] = (
        "'day_entries'" in seg)
    c['THE PAGE DRAWS WHICHEVER ONE IT WAS GIVEN'] = (
        'class="pp-page is-{{ sheet }}"' in page)
    # RG-3, 21 Oct 2026 - the Notes block is gone. It was 240mm of
    # ruled paper under a day that usually holds one or two meals:
    # "Show the Date, and the recipes and then done."
    c['  the day sheet is the date, the meals and nothing else'] = (
        'pp-notes-lines' not in page and 'pp-srv' in page)
    # RG-3, 21 Oct 2026 - the ruled fill is gone with it. The column
    # head stays: a week sheet still names its seven days.
    c['  the week sheet heads each column with its own date'] = (
        'pp-rule' not in page and 'pp-colhead' in page)
    c['  one weekday row for the sheet, not a strip per week'] = (
        'pp-dow-row' in page and 'pp-week-label' not in page)
    # RG-3, 21 Oct 2026 - A MONTH IS. The week and the day are as
    # tall as their content now, which is why only one number is
    # left. test_print_compact measures all three.
    c['THE MONTH SHEET IS EXACTLY ONE PAGE TALL'] = (
        'height: 186mm' in style and 'height: 258mm' not in style)
    c['  and base own furniture is off the paper'] = (
        '.main-content > br' in style
        and '.main-content > center' in style)
    c['  portrait for a day, landscape for the rest'] = (
        'A4 portrait' in style and 'A4 landscape' in style)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

page = T.code_only(NOW[TPL])
style = page[page.find('<style>'):page.find('</style>')]

# GUARDS. True before this round and true after it - a claims() dict
# is a DELTA, and a guard put in it fails the control for being
# correct. See claude/claims_is_a_delta_21_oct.md.
ok('<h2 class="page-title-h2">MEAL PLAN</h2>' in NOW[TPL],
   'the house heading survived the rewrite - test_house_title, '
   'test_heading_prefix and test_heading_standard all read this page')
ok('class="page-subtitle-h4"' in NOW[TPL],
   '  and so did the house subtitle')
# AND NO RULE ON THIS PAGE NAMES EITHER OF THEM. The first draft
# restyled both inside .pp-sheet and test_heading_components named
# this page at once: a shared heading component a page restyles is a
# component that page has forked. The sheet has a masthead of its
# own now, in classes base has never seen.
for _c in ('page-title-h2', 'page-subtitle-h4'):
    ok(not re.search(r'\.%s[\s,.:{>+~\[]' % _c, style),
       '  and no rule on this page names .%s' % _c)
_mk = page[page.index('</style>'):]
ok(_mk.index('page-title-h2') < _mk.index('page-action-buttons'),
   'the title is above the bar - test_bar_top reads all 151 '
   'templates for exactly this, and found this page when the title '
   'moved into the sheet')
ok('pp-eyebrow' in page and 'pp-period' in page and 'pp-count' in page,
   '  while the sheet carries a masthead of its own')
ok(not re.findall(r'#[0-9a-fA-F]{3,8}\b', style),
   'not one literal colour in the stylesheet - the five renders he '
   'chose from were built with hex and none of it came here',
   re.findall(r'#[0-9a-fA-F]{3,8}\b', style)[:6])
ok('repeat(7, minmax(0, 1fr))' in style,
   'the seven tracks can still shrink - a bare 1fr is minmax(AUTO, '
   '1fr) and printed the Sunday column off the paper')
naked = [m.group(1).strip()
         for m in re.finditer(r'@media([^{]*)\{', NOW[TPL])
         if 'max-width' in m.group(1) and 'screen' not in m.group(1)]
ok(not naked,
   'every width query names screen - a bare one prints the phone '
   'layout, which on THIS page would be absurd', naked)
bar = page[page.index('page-action-buttons'):page.index('</div>',
                                                        page.index(
                                                            'action-back'))]
ok(bar.count('action-primary') == 1 and 'action-back' in bar,
   'one primary in the bar and Back behind it - base 3.4')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: before this round not one of these held',
   'what held: %r' % (held,))

oldpage = T.code_only(BEFORE[TPL])
ok('pp-week-label' in oldpage,
   'CONTROL: and every week really did carry its own `Week of` strip')
ok('{% if sheet' not in oldpage,
   'CONTROL: the page could not branch - one layout for every range')
oldstyle = oldpage[oldpage.find('<style>'):oldpage.find('</style>')]
ok('@page { size: landscape;' in oldstyle,
   'CONTROL: and its @page named an ORIENTATION and no paper - so '
   'Chromium printed it on US Letter, 792x612 pt, measured against '
   'the reverted tree while this suite was being written')
oldpin = BEFORE[PINS]
ok("seen.get('day') == (1, 7, 6)" in oldpin,
   'CONTROL: AND THE SUITE AGREED WITH IT. PP-1 pinned "A DAY is '
   'one week of grid with one day lit and six dimmed", and it passed '
   'every time, because that is what the page did')
ok("seen.get('day') == (0, 0, 0)" in NOW[PINS],
   'the pin is inverted in the same patcher that changed the page')


# ==========================================================================
head('3. ON PAPER - FIVE RANGES, PRINTED TO REAL A4')
# ==========================================================================
# EVERYTHING ABOVE IS ABOUT FILES. "A month fits on one A4 page" is a
# sentence until a printer disagrees with it, so this prints five of
# them through Chromium and reads the page count out of the PDF.
#
# THE SIX-WEEK MONTH IS THE ONE THAT MATTERS. August 2026 and
# February 2027 both need six grid rows, and a fixed cell height fits
# five of them and spills the sixth. The sheet is a fixed box and the
# rows share it, so both fill exactly one page.
measured = {}
CASES = (
    ('day', {'from': '2026-10-21', 'to': '2026-10-21'}, 'portrait'),
    ('week', {'from': '2026-10-19', 'to': '2026-10-25'}, 'landscape'),
    ('month5', {'from': '2026-10-01', 'to': '2026-10-31'}, 'landscape'),
    ('month6', {'from': '2026-08-01', 'to': '2026-08-31'}, 'landscape'),
    ('range', {'from': '2026-10-21', 'to': '2026-11-03'}, 'landscape'),
)
html = {}
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
    from pages.models import MealEntry, Recipe
    u = User.objects.create_user(username='rg1', password='x',
                                 email='rg1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    # A BUSY MONTH, AND THE LONGEST NAME IN IT. An empty plan prints
    # on one page whatever the layout does; the question is whether a
    # full one does.
    NAMES = ['Butter Chicken Curry', 'Garlic Naan', 'Spanakopita',
             'Moussaka', 'Lamb Kleftiko', 'Greek Salad', 'Pastitsio',
             'Almond Nougatina', 'Beef Stifado', 'Rice', 'Gemista',
             'Fasolada', 'Amygdalopita', 'Roast Chicken', 'Potatoes',
             'Soutzoukakia', 'Pork Gyros', 'Halloween Pizza',
             'Garlic Bread', 'Chicken Souvlaki']
    rec = dict((n, Recipe.objects.create(recipe_name=n, servings=6,
                                         prep_time=10, cook_time=20))
               for n in NAMES)
    for month in (8, 10):
        for d in range(1, 32):
            when = dt.date(2026, month, d)
            p = MealEntry.objects.create(date=when,
                                         recipe=rec[NAMES[d % 20]],
                                         servings=6, created_by=u)
            if d % 3 == 0:
                MealEntry.objects.create(date=when,
                                         recipe=rec[NAMES[(d + 1) % 20]],
                                         servings=4, created_by=u)
            if d % 4 == 0:
                MealEntry.objects.create(
                    date=when + dt.timedelta(days=1),
                    recipe=rec[NAMES[d % 20]], servings=2,
                    created_by=u, leftover_of=p)
            if d % 7 == 0:
                MealEntry.objects.create(date=when, note='Dinner at Mums',
                                         created_by=u)
    cl = Client()
    cl.force_login(u)
    # EVERY PAGE FETCHED BEFORE A BROWSER IS OPENED. Playwright's sync
    # API runs its own event loop, and the Django ORM called from
    # inside it raises SynchronousOnlyOperation - which looks like a
    # database fault and is not one.
    for name, qs, _ in CASES:
        html[name] = cl.get('/meal_plans/print/',
                            qs).content.decode('utf-8')
except Exception as ex:
    skip('the printed sheets',
         'Django would not start: %s' % str(ex).split('\n')[0][:90])

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
try:
    import pypdf
except Exception:
    pypdf = None

if not html or sync_playwright is None or pypdf is None:
    skip('the five sheets', 'playwright, pypdf or the pages are absent')
else:
    tmp = tempfile.mkdtemp(prefix='alv_printshape_')
    # A SCRATCH DIRECTORY, NEVER THE TREE. CE-1 cost a whole sweep on
    # 20 October because a suite wrote into the repository it was
    # being run against.
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        try:
            for name, _, want in CASES:
                pg = br.new_page()
                pg.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg.set_content(html[name], wait_until='domcontentloaded')
                pg.emulate_media(media='print')
                out = os.path.join(tmp, '%s.pdf' % name)
                pg.pdf(path=out, print_background=True,
                       prefer_css_page_size=True)
                # EVERY MEAL, AGAINST THE EDGE OF ITS SHEET. An
                # ellipsis is the other way a name goes missing, so
                # scrollWidth is asked as well as the geometry.
                spill = pg.evaluate("""() => {
                    const s = document.querySelector('.pp-sheet');
                    if (!s) { return ['no sheet']; }
                    const r = s.getBoundingClientRect();
                    const bad = [];
                    document.querySelectorAll('.pp-meal').forEach(e => {
                        const b = e.getBoundingClientRect();
                        if (b.right > r.right + 0.6
                            || b.left < r.left - 0.6
                            || e.scrollWidth > e.clientWidth + 0.6) {
                            bad.push(e.innerText.trim().slice(0, 24));
                        }
                    });
                    return bad.slice(0, 6);
                }""")
                nmeals = pg.evaluate(
                    "() => document.querySelectorAll('.pp-meal').length")
                pg.close()
                rd = pypdf.PdfReader(out)
                mb = rd.pages[0].mediabox
                measured[name] = {
                    'pages': len(rd.pages),
                    'size': (round(float(mb.width)),
                             round(float(mb.height))),
                    'want': want, 'spill': spill, 'meals': nmeals,
                    'sheet': (re.findall(r'class="pp-page is-(\w+)"',
                                         html[name]) or ['?'])[0],
                }
        finally:
            br.close()

    print('')
    print('  sheet    shape   pages  paper      meals  off the sheet')
    for name, _, _ in CASES:
        m = measured[name]
        print('  %-8s %-7s %-6d %-10s %-6d %s'
              % (name, m['sheet'], m['pages'], '%dx%d' % m['size'],
                 m['meals'], m['spill'] or 'none'))
    print('')

    ok(all(m['pages'] == 1 for m in measured.values()),
       'EVERY ONE OF THE FIVE IS ONE SHEET OF PAPER',
       dict((k, v['pages']) for k, v in measured.items()))
    ok(measured['month6']['pages'] == 1,
       '  INCLUDING A SIX-WEEK MONTH - August 2026 needs six grid '
       'rows and a fixed cell height would have spilled it',
       measured['month6'])
    for name, _, want in CASES:
        w, h = measured[name]['size']
        got = 'portrait' if h > w else 'landscape'
        ok(got == want and sorted((w, h)) == list(A4),
           '  %-7s prints %s A4 - %dx%d pt' % (name, got, w, h),
           measured[name]['size'])
    ok(measured['day']['sheet'] == 'day',
       'A DAY PRINTS A DAY. It printed a week with six columns greyed '
       'out, which is what he reported', measured['day'])
    ok(measured['week']['sheet'] == 'week'
       and measured['month5']['sheet'] == 'month'
       and measured['range']['sheet'] == 'range',
       '  and the other three are what their ranges say they are',
       dict((k, v['sheet']) for k, v in measured.items()))
    ok(all(m['meals'] > 0 for m in measured.values()),
       '  with meals really on them - an empty plan fits any layout',
       dict((k, v['meals']) for k, v in measured.items()))


# ==========================================================================
head('4. NOTHING TRUNCATES')
# ==========================================================================
if not measured:
    skip('the long names', 'nothing was printed')
else:
    spilt = dict((k, v['spill']) for k, v in measured.items() if v['spill'])
    ok(not spilt,
       'NO MEAL IS CLIPPED OR HANGS OFF THE SHEET, at any of the '
       'three sizes - `Amygdalopita` came out `Amygdalo...` in a '
       '130px column while this was being drawn', spilt)
    ok('overflow-wrap: anywhere' in style and 'ellipsis' not in style,
       '  because a name that does not fit WRAPS. On a screen an '
       'ellipsis is a promise you can hover; on paper it is a name '
       'you cannot read')


# ==========================================================================
head('5. PP-1 OWN SUITE, RUN')
# ==========================================================================
# A PIN MOVED IN A PATCHER IS A PIN THAT HAS TO STILL FIT. This round
# rewrote the page test_print_plan measures and edited that suite in
# the same patcher; running it is the only way to know the two
# descriptions have not come apart.
try:
    r = subprocess.run([sys.executable, PPT], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=900)
    out = r.stdout.decode('utf-8', 'replace')
    tail = [ln for ln in out.strip().split('\n') if 'passed' in ln][-1:]
    print('')
    print('  %s' % (tail[0].strip() if tail else '(no summary)'))
    print('')
    ok(r.returncode == 0, 'test_print_plan passes against the new page',
       out[-800:])
    ok('A DAY DRAWS NO GRID AT ALL' in out,
       '  and it says so: its day claim is the inverted one')
except Exception as e:
    skip('PP-1 suite', str(e)[:80])


# ==========================================================================
head('6. SCOPE, REGISTRATION AND THE GATE')
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

# THE CENSUSES THIS ROUND MOVED. Three suites count the whole tree and
# this round redrew a page's entire stylesheet; a pin moved without a
# backup is a pin nobody can put back.
for name, n in (('test_pair_contrast.py', 724),
                ('test_surface_border.py', 95),
                ('test_important_base.py', 771)):
    p = os.path.join(ROOT, name)
    body = read(p)
    ok(MARK in body, '%s carries this round reason for its new number'
       % name)
    ok(os.path.isfile(p + SUFFIX), '  and is backed up')
    ok(str(n) in body, '  and the number it was measured at is %d' % n)

patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_print_shape as PATCH                           # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
