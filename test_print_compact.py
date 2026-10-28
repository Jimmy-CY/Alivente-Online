# -*- coding: utf-8 -*-
"""test_print_compact.py - round RG-3, 21 Oct 2026.

A SHEET SHOULD BE AS TALL AS WHAT IS ON IT.

    "I don't like the Weekly Print. The days' height should basically
     be the last recipe (in the day that has the most recipes). The
     same with the Day Print. Just wasting space. Show the Date, and
     the recipes and then done."

HE PICKED B2 AND C2 FROM A RENDER AND CHANGED HIS MIND ON PAPER.
That is the right way round. B2's lower half was ruled so the sheet
could be written on; C2 had a Notes block under the day for the same
reason. Neither survives a real week - his own has one meal on four
of the seven days, so what came out of the printer was seven columns
of ruled emptiness under five words.

THE MONTH IS UNTOUCHED AND STILL FILLS ITS SHEET. Fitting a whole
month on one sheet of A4 is the entire point of that layout, and he
said the month looked good.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The ruled fill and the Notes block are gone from
      the rules AND the markup, and only the month keeps a height.

  2   THE CONTROL. Re-asked of .bak_printcompact, where all three
      sheets filled a page.

  3   MEASURED ON PAPER. Three shapes printed to real A4 through
      Chromium: the sheet height in millimetres and the page count
      read out of the PDF.

  4   AND THE HEIGHT FOLLOWS THE CONTENT, which is the whole claim.
      The same week with one meal a day and with four is measured
      twice, and the busy one is taller. A fixed height would give
      the same number for both - which is the fault.

  5   RG-1's OWN SUITE, RUN. This round corrects three of its claims
      in the same patcher.

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

SUFFIX = '.bak_printcompact'
ME = 'test_print_compact.py'
PATCHER = 'apply_print_compact.py'
PS1 = 'Push-PendingChanges.ps1'
SHAPE = 'test_print_shape.py'
MARK = 'RG-3, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_print.html')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL,)

MM = 96 / 25.4          # CSS pixels per millimetre at 96dpi
A4 = (595, 842)         # PostScript points, which is what a MediaBox is in
# A WEEK THAT FILLED ITS PAGE WAS 186mm. Anything under a third of
# that is unambiguously "as tall as its content" rather than "nearly
# as tall as the page".
ROOMY = 90.0

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

GONE = ('pp-rule', 'pp-notes', 'pp-notes-label', 'pp-notes-lines')


def claims(bundle):
    page = T.code_only(bundle[TPL])
    style = page[page.find('<style>'):page.find('</style>')]
    c = {}
    c['THE RULED FILL AND THE NOTES BLOCK ARE GONE - the finding'] = (
        not any(d in page for d in GONE))
    c['  and they left with their markup, not behind display:none'] = (
        'display: none' not in style.split('.pp-rule')[-1][:40])
    c['ONLY THE MONTH STILL FILLS A SHEET'] = (
        'height: 186mm' in style and 'height: 258mm' not in style)
    c['  the week sheet has no height of its own'] = (
        not re.search(r'\.is-week\s+\.pp-sheet\s*\{[^}]*height:\s*\d',
                      style))
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

page = T.code_only(NOW[TPL])
style = page[page.find('<style>'):page.find('</style>')]
markup = page[page.find('</style>'):]

# GUARDS. True before this round and true after it - a claims() dict
# is a DELTA, and a guard put in it fails the control for being
# correct. Seventh time this shape has come up today.
ok('pp-colhead' in markup,
   'the week still heads each column with its own date - the sheet got '
   'shorter, not plainer')
ok('pp-srv' in markup, 'and the day still says how many it serves')
for probe in ('A4 portrait', 'A4 landscape'):
    ok(probe in style, 'both orientations survive: %s' % probe)
ok('repeat(7, minmax(0, 1fr))' in style,
   'the seven tracks can still shrink - a bare 1fr printed the Sunday '
   'column off the paper')
ok('overflow-wrap: anywhere' in style and 'ellipsis' not in style,
   'and a long name still wraps rather than truncating')
naked = [m.group(1).strip()
         for m in re.finditer(r'@media([^{]*)\{', NOW[TPL])
         if 'max-width' in m.group(1) and 'screen' not in m.group(1)]
ok(not naked, 'every width query still names screen', naked)
ok(not re.findall(r'#[0-9a-fA-F]{3,8}\b', style),
   'and not one literal colour',
   re.findall(r'#[0-9a-fA-F]{3,8}\b', style)[:5])


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
oldpage = T.code_only(BEFORE[TPL])
oldstyle = oldpage[oldpage.find('<style>'):oldpage.find('</style>')]
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: before this round not one of these held',
   'what held: %r' % (held,))
ok(all(d in oldpage for d in ('pp-rule', 'pp-notes-lines')),
   'CONTROL: the ruled fill and the Notes block were both really there')
ok('height: 258mm' in oldstyle,
   'CONTROL: and the day really did fill a page')
ok(re.search(r'\.is-week\s+\.pp-sheet\s*\{[^}]*186mm', oldstyle)
   is not None
   or '.is-week .pp-sheet { height: 186mm' in oldstyle
   or re.search(r'\.is-month \.pp-sheet,\s*\n\s*\.is-week \.pp-sheet',
                oldstyle) is not None,
   'CONTROL: and so did the week')


# ==========================================================================
head('3. MEASURED ON PAPER')
# ==========================================================================
# EVERYTHING ABOVE READS A STYLESHEET. "As tall as its content" is a
# claim about a layout engine and a sheet of paper, so three shapes
# are printed to real A4 and the heights and page counts come back
# out of the PDF.
measured = {}
html = {}
CASES = (('week', {'from': '2026-10-19', 'to': '2026-10-25'}, 'landscape'),
         ('day', {'from': '2026-10-21', 'to': '2026-10-21'}, 'portrait'),
         ('month', {'from': '2026-10-01', 'to': '2026-10-31'}, 'landscape'))
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
    u = User.objects.create_user(username='rg3', password='x',
                                 email='rg3@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    NAMES = ['Lamb Kleftiko', 'Greek Salad', 'Pastitsio', 'Moussaka',
             'Gemista', 'Spaghetti Bolognaise', 'Pepper Sauce']
    rec = dict((n, Recipe.objects.create(recipe_name=n, servings=6,
                                         prep_time=10, cook_time=30))
               for n in NAMES)
    # HIS OWN WEEK, as the screenshot showed it: a few single meals
    # and one day carrying three. A full month either side, so the
    # month shape has something to fill a sheet with.
    for d, ns in ((21, ['Gemista']), (22, ['Pepper Sauce']),
                  (23, ['Spaghetti Bolognaise', 'Greek Salad',
                        'Pastitsio']),
                  (24, ['Moussaka']), (25, ['Pepper Sauce'])):
        for n in ns:
            MealEntry.objects.create(date=dt.date(2026, 10, d),
                                     recipe=rec[n], servings=6,
                                     created_by=u)
    for d in range(1, 19):
        MealEntry.objects.create(date=dt.date(2026, 10, d),
                                 recipe=rec[NAMES[d % 7]], servings=6,
                                 created_by=u)
    cl = Client()
    cl.force_login(u)
    # FETCHED BEFORE A BROWSER IS OPENED. Playwright's sync API runs
    # its own event loop and the ORM called from inside it raises
    # SynchronousOnlyOperation, which looks like a database fault.
    for name, qs, _ in CASES:
        html[name] = cl.get('/meal_plans/print/',
                            qs).content.decode('utf-8')
    # AND THE SAME WEEK, BUSY. Section 4 needs a second measurement
    # of the one shape whose height is supposed to move.
    for d in (19, 20, 21, 22, 23, 24, 25):
        for n in NAMES[:4]:
            MealEntry.objects.create(date=dt.date(2026, 10, d),
                                     recipe=rec[n], servings=6,
                                     created_by=u)
    html['week_busy'] = cl.get(
        '/meal_plans/print/',
        {'from': '2026-10-19', 'to': '2026-10-25'}).content.decode('utf-8')
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
    skip('the three sheets', 'playwright, pypdf or the pages are absent')
else:
    # A SCRATCH DIRECTORY, NEVER THE TREE. CE-1 cost a whole sweep on
    # 20 October because a suite wrote into the repository it was
    # being run against.
    tmp = tempfile.mkdtemp(prefix='alv_printcompact_')
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        try:
            for name in list(html):
                land = not name.startswith('day')
                w = (297 - 24) if land else (210 - 36)
                h = (210 - 22) if land else (297 - 36)
                pg = br.new_page(viewport={'width': round(w * MM),
                                           'height': round(h * MM)})
                pg.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg.set_content(html[name],
                               wait_until='domcontentloaded')
                pg.emulate_media(media='print')
                pg.wait_for_timeout(250)
                tall = pg.evaluate(
                    "() => {const e = document.querySelector('.pp-sheet');"
                    " return e ? Math.round("
                    "e.getBoundingClientRect().height) : -1;}")
                out = os.path.join(tmp, '%s.pdf' % name)
                pg.pdf(path=out, print_background=True,
                       prefer_css_page_size=True)
                pg.close()
                rd = pypdf.PdfReader(out)
                mb = rd.pages[0].mediabox
                measured[name] = {
                    'mm': tall / MM, 'px': tall,
                    'pages': len(rd.pages),
                    'size': (round(float(mb.width)),
                             round(float(mb.height)))}
        finally:
            br.close()

    print('')
    print('  sheet        height      paper       pages')
    for name in ('day', 'week', 'week_busy', 'month'):
        m = measured.get(name)
        if m:
            print('  %-12s %5.0fmm      %-10s %d'
                  % (name, m['mm'], '%dx%d' % m['size'], m['pages']))
    print('')
    ok(all(m['pages'] == 1 for m in measured.values()),
       'every sheet is still ONE page of paper',
       dict((k, v['pages']) for k, v in measured.items()))
    for name, _, want in CASES:
        m = measured.get(name)
        if not m:
            continue
        w, h = m['size']
        got = 'portrait' if h > w else 'landscape'
        ok(got == want and sorted((w, h)) == list(A4),
           '  %-6s is still %s A4' % (name, want), m['size'])
    ok(measured['week']['mm'] < ROOMY,
       'THE WEEK IS AS TALL AS ITS CONTENT: %.0fmm, where it filled '
       '186mm this morning' % measured['week']['mm'],
       measured['week']['mm'])
    ok(measured['day']['mm'] < 70,
       'AND SO IS THE DAY: %.0fmm, where it filled 258mm'
       % measured['day']['mm'], measured['day']['mm'])
    ok(180 <= measured['month']['mm'] <= 190,
       'while the MONTH still fills its sheet at %.0fmm - which is the '
       'point of the month' % measured['month']['mm'],
       measured['month']['mm'])


# ==========================================================================
head('4. AND THE HEIGHT FOLLOWS THE CONTENT')
# ==========================================================================
# THE WHOLE CLAIM, AND THE ONLY ONE A SINGLE MEASUREMENT CANNOT MAKE.
# A sheet fixed at 55mm would satisfy every number in section 3. The
# same week is measured twice - his, and the same seven days with
# four meals on each - and the busy one has to be taller.
if 'week_busy' not in measured:
    skip('the busy week', 'nothing was measured')
else:
    sparse, busy = measured['week']['mm'], measured['week_busy']['mm']
    print('')
    print('  the same seven days, measured twice:')
    print('     his week   (7 meals, one day with three)  %5.0fmm' % sparse)
    print('     busy week  (28 meals, four every day)     %5.0fmm' % busy)
    print('')
    ok(busy > sparse + 10,
       'A BUSIER WEEK IS A TALLER SHEET - %.0fmm against %.0fmm. A '
       'fixed height would have given the same number twice, which is '
       'the fault' % (busy, sparse), (sparse, busy))
    ok(measured['week_busy']['pages'] == 1,
       '  and it is still one page',
       measured['week_busy']['pages'])
    ok(busy < 186,
       '  and still shorter than the page it used to fill',
       busy)


# ==========================================================================
head('5. RG-1 OWN SUITE, RUN')
# ==========================================================================
# This round corrects three of its claims in the same patcher. A
# claim moved is a claim that has to still fit.
# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN test_print_shape IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims it was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(SHAPE) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(SHAPE))
ok('the date, the meals and nothing else' in read(os.path.join(ROOT, SHAPE)),
   '  and it records that the Notes block went')


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
ok(os.path.isfile(os.path.join(ROOT, SHAPE) + SUFFIX),
   'and so is RG-1 own suite, which this round corrects')
ok(MARK in read(os.path.join(ROOT, SHAPE)),
   '  which carries this round reason for the correction')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_print_compact as PATCH                         # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
