# -*- coding: utf-8 -*-
"""test_print_plan.py - round PP-1, 20 Oct 2026.

A MEAL PLAN YOU CAN PUT ON THE FRIDGE.

Demetri, 20 Oct 2026:

    "I would like to be able to print a month, week of day in a
     presentable format. Also, I should be able to select To and From
     Dates and print a Meal Plan."

There was no print support on the planner at all. The only mention of
the word on that screen was a comment explaining the print-leak rule.

HE CHOSE A SEPARATE PAGE over a print stylesheet on the planner, and
A WEEK-GRID PER WEEK over a day-by-day list. Both answers are in the
shape of this round: a new view, a new route, a new template, and one
button on the planner carrying the two dates SL-7 already computes.

WHOLE WEEKS, EDGES DIMMED. A range that starts on a Wednesday has a
ragged first week, and three empty cells at the front of a
seven-column grid read as missing data rather than as a boundary. So
the grid always runs Monday to Sunday and the days outside the range
are marked out-of-range for the template to grey.

THREE THINGS HERE WERE FOUND BY DRIVING IT, NOT BY READING IT, and
each has a claim of its own below:

  A   The page wore .calendar-container, which is what the PLANNER
      wraps itself in - and which the planner DEFINES. On this page
      the name carried no rules and the grid ran flush to both edges
      of the window. A class is not a style.

  B   `repeat(7, 1fr)` is `repeat(7, minmax(auto, 1fr))`, so the
      tracks would not shrink below the widest word in the cell;
      and base wraps every page in a Bootstrap .container whose
      max-width is set inside a min-width query, which applies to
      PAPER. Measured on a sheet: 992px of grid, 794px of paper,
      and Sunday printed off the edge.

  C   The Print button is an .action-secondary, and base hides every
      secondary below 768px IN A BAR THAT HAS A MORE MENU. At 390px
      it came back display:none, height 0. The standard says what to
      do about it: "check the menu lists them."

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The view, the page and the two ways in.

  2   THE CONTROL. Re-asked of the pre-round files, where none of it
      existed and the planner could not print at all.

  3   ASKED OF THE SERVER: six ranges, and the grid each one draws.

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

SUFFIX = '.bak_printplan'
ME = 'test_print_plan.py'
PATCHER = 'apply_print_plan.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PP-1, 20 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
PRINTP = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_print.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
GATE = os.path.join(ROOT, PS1)

# THE THREE THAT WERE THERE BEFORE have a backup to re-ask. The fourth
# is CREATED by this round, so there is nothing of it to re-ask - and a
# control that demanded one would simply crash.
FILES = (VIEW, URLS, TPL)
MADE = (PRINTP,)

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
# THE PAGE THIS ROUND CREATES, READ SOFTLY.
#
# Against a reverted tree that file is gone, and `read()` on it would
# raise before section 1 ran - a crash, where the house asks for a
# failure. An empty string makes every claim about the page come back
# false, which is exactly what is true when the page is not there.
for _p in MADE:
    NOW[_p] = read(_p) if os.path.isfile(_p) else ''


def claims(bundle, page):
    """Everything this round asserts, asked of whatever it is handed.

    `page` is passed separately because the fourth file does not exist
    before the round and the control has to ask the three that do.
    """
    # THE FUNCTION, NOT THE FILE.
    #
    # Four of the claims below held in the CONTROL, against the tree
    # as it was before this round - and they were right to. A from/to
    # pair, a reversed pair swapped, a 92-day ceiling and a one-pass
    # fetch are all things meal_shopping_list already does, and it
    # lives in this same module. Asked of the file, those four say
    # "somebody here does this"; asked of the function, they say what
    # this round actually claims: that THIS view does.
    whole = T.python_code_only(bundle[VIEW], payloads=True)
    if 'def meal_plan_print' in whole:
        code = whole[whole.index('def meal_plan_print'):]
        nxt = re.search(r'\n@|\ndef ', code[1:])
        code = code[:nxt.start() + 1] if nxt else code
    else:
        code = ''
    urls = bundle[URLS]
    nt = T.code_only(bundle[TPL])
    c = {}

    # ---- THE VIEW
    c['THE PLAN CAN BE PRINTED - the finding'] = (
        'def meal_plan_print' in whole)
    c['  from a from/to pair, the shopping list pair'] = (
        "week_of(request.GET.get('from')" in code
        and "week_of(request.GET.get('to')" in code)
    c['  the grid begins on a Monday, so no week starts ragged'] = (
        'monday_of(start)' in code)
    c['  and the days outside the range are still known'] = (
        "'in_range'" in code)
    c['  one query for the whole grid, not one per day'] = (
        'for e in (MealEntry.objects' in code
        and code.count('MealEntry.objects') == 1)
    c['  the same 13-week ceiling the shopping list has'] = (
        '(end - start).days > 92' in code)
    c['  and a reversed pair is read, not refused'] = (
        'start, end = end, start' in code)

    # ---- THE ROUTE
    c['  there is a route to it'] = (
        "name='meal_plan_print'" in urls)

    # ---- THE PAGE
    c['THE PAGE IS A WEEK-GRID PER WEEK'] = (
        'pp-grid' in page and 'repeat(7,' in page)
    c['  it dims the days outside the range'] = ('is-out' in page)
    # A - the fault that only the layout engine could see.
    #
    # ASKED OF THE MARKUP, NOT THE FILE. The first form of this claim
    # was `'calendar-container' not in page`, and it failed against
    # the fixed page - because the comment EXPLAINING why that class
    # was wrong contains the name. A thing and something that merely
    # names the thing are not the same thing; it is the class
    # attribute that has to be clean, not the prose.
    c['  and it styles its own container'] = (
        # RG-1, 21 Oct 2026 - the attribute reads `pp-page is-month`
        # now, so the exact-string form stopped matching a page that
        # is still doing the right thing. A word boundary asks the
        # question PP-1 meant: is this page wearing its OWN container
        # rather than one meal_planner.html defines?
        bool(re.search(r'class="pp-page\b', page))
        and 'class="calendar-container"' not in page)
    # B - two of them, both measured on paper.
    c['  tracks that can shrink: minmax(0, 1fr)'] = (
        'repeat(7, minmax(0, 1fr))' in page)
    c['  and a print block that releases the Bootstrap container'] = (
        '@media print' in page
        and 'max-width: none !important'
        in page[page.index('@media print'):] if '@media print' in page
        else False)
    c['  landscape, because the thing printed is seven columns wide'] = (
        '@page' in page and 'landscape' in page)

    # ---- THE TWO WAYS IN
    c['THE PLANNER LINKS TO IT'] = ('meal_plan_print' in nt)
    c['  carrying the range SL-7 computes, on every link'] = all(
        'sl_from' in seg[:260] and 'sl_to' in seg[:260]
        for seg in nt.split('meal_plan_print')[1:]) and (
            len(nt.split('meal_plan_print')) > 1)
    # C - the one a phone found.
    c['  and the More menu lists it, so a phone can reach it'] = (
        'action-more-menu' in nt
        and 'meal_plan_print' in nt[nt.index('action-more-menu'):])
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW, NOW[PRINTP]).items():
    ok(got, msg)

# EVERY WIDTH QUERY ON THIS PAGE NAMES screen.
#
# The 21 September print-leak rule: a clause naming no media type
# matches print as well, so a phone layout written as a bare
# `(max-width: ...)` is also what comes out of the printer. On the one
# page in this project whose whole purpose is printing, getting that
# wrong would be absurd - so it is asked here rather than assumed.
naked = [m.group(1).strip()
         for m in re.finditer(r'@media([^{]*)\{', NOW[PRINTP])
         if 'max-width' in m.group(1) and 'screen' not in m.group(1)]
ok(not naked,
   'every width query on this page names screen - a bare one would '
   'print the phone layout', naked)

# AND EVERY CLASS THE MARKUP WEARS IS STYLED SOMEWHERE IT CAN SEE.
# This is finding A as a rule rather than as one name: .pp-page was
# .calendar-container, which meal_planner.html defines and this page
# cannot see. Ask the tree, don't type a list.
own = T.code_only(NOW[PRINTP])
sheets = own + '\n' + T.code_only(read(BASE))
VENDOR = ('btn', 'fa', 'fas', 'far', 'fab', 'col', 'row', 'container',
          'fa-', 'd-', 'ml-', 'mr-', 'mt-', 'mb-', 'px-', 'py-',
          'text-', 'bg-', 'table', 'form-', 'modal', 'input-',
          'custom-', 'badge', 'close', 'sr-only')
homeless = []
# .find(), not .index(): a missing page is a FAILED claim above, not
# a ValueError here. test_pick_note crashed on exactly this.
body = own[own.find('</style>') + 1:] if '</style>' in own else ''
for attr in re.findall(r'class="([^"{}]*)"', body):
    for cls in attr.split():
        if not cls or cls in homeless:
            continue
        if cls in VENDOR or any(cls.startswith(v) for v in VENDOR
                                if v.endswith('-')):
            continue
        if re.search(r'\.%s[\s,.:{>+~\[]' % re.escape(cls), sheets):
            continue
        homeless.append(cls)
ok(not homeless,
   'every class on this page has a rule it can see - on this page, in '
   'base, or behind a vendor prefix', homeless)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
# THE FOURTH FILE DID NOT EXIST, which is the control for the page
# half of every claim above.
ok(not os.path.isfile(PRINTP + SUFFIX),
   'CONTROL: there is no backup of the printable page, because this '
   'round creates it')
held = [m for m, got in claims(BEFORE, '').items() if got]
ok(not held,
   'CONTROL: before this round not one of these claims held',
   'what held: %r' % (held,))
oldv = T.python_code_only(BEFORE[VIEW], payloads=True)
ok('def meal_plan_print' not in oldv,
   'CONTROL: there was no view to print a plan')
oldt = T.code_only(BEFORE[TPL])
ok('print' not in oldt.lower().replace('print-leak', ''),
   'CONTROL: and on the planner the word print appeared only in a '
   'comment about the print-leak rule',
   [l for l in BEFORE[TPL].split('\n') if 'print' in l.lower()][:4])


# ==========================================================================
head('3. SIX RANGES, ASKED OF THE SERVER')
# ==========================================================================
# WHAT CANNOT BE READ OUT OF THE SOURCE. "Whole weeks with the edges
# dimmed" is a sentence until something counts the cells: a month is
# five weeks of grid holding 31 in-range days and four dimmed ones, a
# single day is one week of grid holding one. Ask for all six.
seen, shapes, planner = {}, None, {}
sheets_seen = {}          # RG-1, 21 Oct 2026
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
    u = User.objects.create_user(username='pp1', password='x',
                                 email='pp1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r1 = Recipe.objects.create(recipe_name='Almond Nougatina',
                               servings=6, prep_time=10, cook_time=20)
    # A MEAL, ITS LEFTOVERS AND A NOTE - the three shapes a cell can
    # hold, so all three branches of the template are drawn and not
    # just the one.
    first = MealEntry.objects.create(date=dt.date(2026, 10, 21),
                                     recipe=r1, servings=6,
                                     created_by=u)
    MealEntry.objects.create(date=dt.date(2026, 10, 23), recipe=r1,
                             servings=2, created_by=u,
                             leftover_of=first)
    MealEntry.objects.create(date=dt.date(2026, 10, 27),
                             note='Dinner at Mums', created_by=u)
    cl = Client()
    cl.force_login(u)
    url = reverse('meal_plan_print')

    def grid(qs):
        h = cl.get(url, qs).content.decode('utf-8')
        return {
            'weeks': h.count('class="pp-week"'),
            'cells': len(re.findall(r'class="pp-day(?:[ "])', h)),
            'out': len(re.findall(r'class="pp-day is-out', h)),
            # RG-1, 21 Oct 2026 - which of the four sheets came back.
            # A day is no longer a week with six columns greyed out,
            # so the count of cells is not on its own a description of
            # what was printed.
            'sheet': (re.findall(r'class="pp-page is-(\w+)"', h) or
                      ['?'])[0],
            'html': h,
        }

    for name, qs in (
            ('day', {'from': '2026-10-20', 'to': '2026-10-20'}),
            ('week', {'from': '2026-10-19', 'to': '2026-10-25'}),
            ('month', {'from': '2026-10-01', 'to': '2026-10-31'}),
            ('ragged', {'from': '2026-10-21', 'to': '2026-11-03'}),
            # RG-1, 21 Oct 2026 - the same dates under the name the
            # page now gives that shape.
            ('range', {'from': '2026-10-21', 'to': '2026-11-03'}),
            ('reversed', {'from': '2026-10-31', 'to': '2026-10-01'}),
            ('nothing', {})):
        g = grid(qs)
        seen[name] = (g['weeks'], g['cells'], g['out'])
        sheets_seen[name] = g['sheet']   # RG-1, 21 Oct 2026
        if name == 'ragged':
            h = g['html']
            shapes = (h.count('pp-meal is-left'),
                      h.count('pp-meal is-note'),
                      len(re.findall(r'class="pp-meal"', h)))
    # AND THE TWO WAYS IN, from the planner itself, per view.
    for v in ('month', 'week', 'day'):
        h = cl.get('/meal_plans/', {'view': v, 'date': '2026-10-20'}
                   ).content.decode('utf-8')
        planner[v] = re.findall(
            # [^"]*" RATHER THAN " - PT-1, 22 Oct 2026. The link now
            # carries the origin after the two dates, and this regex
            # ended at the quote that used to follow ?to=. What it
            # claims is unchanged: from and to are the period of the
            # view you are on.
            r'href="/meal_plans/print/\?from=([0-9-]+)&amp;'
            r'to=([0-9-]+)[^"]*"',
            h)
except Exception as e:
    skip('the asked checks',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if not seen:
    skip('the six ranges', 'nothing was asked')
else:
    print('')
    print('  weeks of grid / cells drawn / dimmed:')
    for k in ('day', 'week', 'month', 'ragged', 'reversed', 'nothing'):
        print('    %-9s %s' % (k, seen.get(k)))
    print('  the ragged range: leftover %s, note %s, plain %s'
          % (shapes or ('?', '?', '?')))
    print('  planner links   : %s' % planner)
    print('')
    # EVERY GRID IS WHOLE WEEKS. Cells = 7 x weeks, always, which is
    # the design decision this round turns on, asked of six answers
    # rather than argued once.
    ragged = [k for k, v in seen.items() if v and v[1] != v[0] * 7]
    ok(not ragged,
       'EVERY range draws whole weeks - seven cells per week, no '
       'week part-drawn', ragged)
    # RG-1, 21 Oct 2026 - THIS CLAIM IS THE FAULT, INVERTED.
    #
    # It read: "A DAY is one week of grid with one day lit and six
    # dimmed" - (1, 7, 6) - and it passed, every time, because that
    # is exactly what the page did. Demetri reported it as "Day view
    # Print, prints a Week view", and he was right: it was a week.
    # The suite measured the thing and agreed with it.
    #
    # A day is now a day sheet: no grid, no cells, nothing dimmed.
    ok(seen.get('day') == (0, 0, 0),
       'A DAY DRAWS NO GRID AT ALL - RG-1. It was (1, 7, 6): one '
       'week of grid with six columns greyed out, which is what '
       '"Day view Print, prints a Week view" was',
       seen.get('day'))
    ok(sheets_seen.get('day') == 'day',
       '  and the page says which sheet it is', sheets_seen.get('day'))
    ok(sheets_seen.get('week') == 'week'
       and sheets_seen.get('month') == 'month'
       and sheets_seen.get('range') == 'range',
       '  as do the other three - the range decides the sheet',
       sheets_seen)
    ok(seen.get('week') == (1, 7, 0),
       'A WEEK fills its grid exactly - nothing to dim',
       seen.get('week'))
    ok(seen.get('month') == (5, 35, 4),
       'A MONTH is five weeks of grid: 31 days of October and four '
       'dimmed - 28, 29, 30 Sep and 1 Nov', seen.get('month'))
    ok(seen.get('ragged') == (3, 21, 7),
       'A RAGGED RANGE, Wed 21 Oct to Tue 3 Nov, is three weeks of '
       'grid with seven dimmed at the two edges', seen.get('ragged'))
    ok(seen.get('reversed') == seen.get('month'),
       'AND A PAIR THE WRONG WAY ROUND is read, not refused - 31 Oct '
       'to 1 Oct draws the month', seen.get('reversed'))
    ok(seen.get('nothing') == (1, 7, 0),
       'with no dates at all it is this week', seen.get('nothing'))
    # THE THREE SHAPES A CELL CAN HOLD.
    ok(shapes == (1, 1, 1),
       'and a cell draws a meal, a leftover and a note differently - '
       'one of each in the range asked for', shapes)
    # THE LINKS, which is SL-7's range reaching this page.
    ok(planner.get('month') == [('2026-10-01', '2026-10-31')] * len(
        planner.get('month') or [1]) and planner.get('month'),
       'the planner on MONTH offers to print the month',
       planner.get('month'))
    ok(planner.get('week') and all(
        p == ('2026-10-19', '2026-10-25') for p in planner['week']),
       'on WEEK, the week', planner.get('week'))
    ok(planner.get('day') and all(
        p == ('2026-10-20', '2026-10-20') for p in planner['day']),
       'and on DAY, that day', planner.get('day'))
    # TWO LINKS, NOT ONE: the bar for a desktop and the More menu for
    # a phone, because base hides the bar's secondary below 768px.
    ok(len(planner.get('week') or []) == 2,
       'and there are TWO of them on the page - the bar, which a '
       'phone hides, and the More menu, which is where it hid it',
       planner.get('week'))


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
import apply_print_plan as PATCH                            # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (
    os.path.join('pages', 'templates', 'meal_plan_print.html'),),
   'and declares the one file it creates, so a revert knows to '
   'delete it', getattr(PATCH, 'CREATES', None))


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
