# -*- coding: utf-8 -*-
"""test_day_order.py - round RO-1, 21 Oct 2026.

THE DAY CARD HAD NO WAY TO SAY WHAT COMES FIRST.

Demetri, 21 October:

    "For the reordering, do we need the buttons. Can we not just have
     like three lines or something that somebody clicks on and then
     drags and drops (similar to Ingredients and Instructions
     entry)???"

SO IT IS THE HANDLE THIS APPLICATION ALREADY HAS. preview_imported_recipe
has dragged ingredients and instructions with SortableJS 1.15.0 since it
was written. Section 1 reads that page and holds this round to its
version, its URL and its four class names rather than quoting them from
a docstring.

THE COLUMN WAS ALWAYS THERE AND NOTHING COULD WRITE IT. sort_order has
decided the order of a day since MN-1; every endpoint that makes a row
appends. reorder_meal_day is the first thing in the system that moves a
row WITHIN its date, and section 3 drives it - including the three ways
it must refuse.

IT REFUSES RATHER THAN GUESSES. An order that is not exactly the rows
on that date is answered 409 WITH THE REAL ORDER. A page left open while
somebody else cooked would otherwise write an order that silently drops
what it never knew about.

THE GRIP IS NOT DRAWN UNTIL THE LIBRARY ANSWERS, and section 4 proves
that in a browser rather than in the stylesheet: the page is rendered
twice, once with Sortable 1.15.0 really served and once with the CDN
failing, and the handle is measured both times. Then a REAL DRAG, with
a real mouse, and the POST it produces is caught and read.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One endpoint, edit-tier, POST-only; one wrapper
      round the rows; a grip on all three row shapes; the idiom read
      off the page that already uses it.

  2   THE CONTROL. Re-asked of .bak_dayorder, where nothing could
      write sort_order at all.

  3   DRIVEN. Three meals, dragged into a new order, read back out of
      the database. Then a stale order, a duplicate, a junk date, a
      GET and a reader without permission.

  4   RENDERED. The grip with the library and without it, measured in
      Chromium; then a real drag, and the request it sends.

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

import io
import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_dayorder'
ME = 'test_day_order.py'
PATCHER = 'apply_day_order.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'RO-1, 21 Oct 2026'
# VS-1, 29 Oct 2026 - the library is served from the app now, not the CDN.
SORTABLE = "{% static 'vendor/sortablejs/Sortable.min.js' %}"

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
PREVIEW = os.path.join(ROOT, 'pages', 'templates',
                       'preview_imported_recipe.html')
GATE = os.path.join(ROOT, PS1)
FILES = (VIEW, URLS, TPL)

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


def claims(d):
    v = T.python_code_only(d[VIEW], payloads=True)
    t = d[TPL]
    css = T.code_only(t)
    js = T.code_only_js(t)
    return {
        'there is an endpoint that moves a row WITHIN its day':
            'def reorder_meal_day' in v,
        '  and it is routed':
            "name='reorder_meal_day'" in d[URLS],
        '  it refuses an order that is not exactly the rows on that day':
            'set(ids) != set(on_day)' in v,
        '  and answers 409 with the real order, so the page can put '
        'itself right':
            ("'order': on_day" in v and 'status=409' in v),
        'the rows have a wrapper of their own to be sorted in':
            'class="day-rows"' in t,
        '  carrying the date, which the endpoint asks for':
            'data-day=' in t,
        'all three row shapes have a grip':
            css.count('class="drag-handle"') == 3,
        '  hidden until the library answers':
            '.day-rows .drag-handle { display: none; }' in css,
        '  and the script only shows it when Sortable is really there':
            ("typeof Sortable === 'undefined'" in js
             and "classList.add('is-draggable')" in js),
        'the page loads SortableJS':
            SORTABLE in t,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# .find(), NOT .index(). Against the reverted tree there is no such
# function and .index() raised ValueError - the suite CRASHED rather
# than failing, which blocks a push exactly as hard and says far less
# about why. Fifth time today, and the lesson keeps arriving in a new
# costume.
V = T.python_code_only(NOW[VIEW], payloads=True)
_a, _b = V.find('def reorder_meal_day'), V.find('def remove_meal_entry')
RV = V[_a:_b] if 0 <= _a < _b else ''
RAW = NOW[VIEW]
_r = RAW.find('def reorder_meal_day')
DECOR = RAW[max(0, _r - 220):_r] if _r >= 0 else ''

ok('@require_POST' in DECOR,
   'the endpoint is POST-only - an order is a write')
ok("permission_required('auth.can_edit_recipes'" in DECOR,
   '  and edit-tier, like everything else that writes')
ok('len(set(ids)) != len(ids)' in RV,
   'the same row sent twice is refused rather than renumbered')
ok('with transaction.atomic():' in RV,
   'the renumber happens inside a transaction - half an order is worse '
   'than the old one')
ok('enumerate(ids, start=1)' in RV,
   '  and it writes 1..N, not 0..N-1, which is what every other writer '
   'on this model already means by sort_order')

# THE IDIOM IS READ OFF THE PAGE THAT ALREADY USES IT. If
# preview_imported_recipe ever changes library or version, this round
# is the thing that would silently disagree - so it is asked, not
# remembered.
PREV = read(PREVIEW)
ok(SORTABLE in PREV,
   'preview_imported_recipe loads the SAME library at the SAME version')
JS = T.code_only_js(NOW[TPL])
PJS = T.code_only_js(PREV)
for opt in ("handle: '.drag-handle'", "ghostClass: 'sortable-ghost'",
            "dragClass: 'sortable-drag'", "chosenClass: 'sortable-chosen'",
            'animation: 150'):
    ok(opt in JS and opt in PJS,
       '  and both pages drag with %s' % opt,
       'planner %s, preview %s' % (opt in JS, opt in PJS))
ok('fa-grip-vertical' in NOW[TPL] and 'fa-grip-vertical' in PREV,
   '  and both wear the same glyph - three lines, which is what he '
   'asked for')

# THE BUTTONS STAY. RD-2's Move answers a different question.
ok('data-move=' in NOW[TPL],
   'GUARD: Move to another day is STILL on the card - dragging says '
   'what comes first on this day, Move says which day')
ok('icon-delete' in NOW[TPL] and 'openLeftover(' in NOW[TPL],
   'GUARD: and so are Remove and Leftovers')

# THE SORTABLE IS BOUND TO THE ROWS, NOT THE BODY. The body also holds
# Add Recipe and Add Note.
ok("querySelector('.day-rows')" in JS,
   'the sortable is bound to the row wrapper, so nothing can be dropped '
   'below the Add buttons')
ok(NOW[TPL].count('<div class="day-rows"') == 1
   and NOW[TPL].count('{# .day-rows - RO-1') == 2,
   '  and the wrapper opens once and closes once', NOW[TPL].count(
       '<div class="day-rows"'))


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

oldv = T.python_code_only(BEFORE[VIEW], payloads=True)
ok('sort_order' in oldv,
   'CONTROL: sort_order was already deciding the order of a day')
ok('def reorder' not in oldv,
   'CONTROL: and NOTHING in the module could write it - every endpoint '
   'appended')
ok(oldv.count("Max('sort_order')") >= 3,
   'CONTROL: three or more writers each asked for the TAIL, which is '
   'the only thing they could do', oldv.count("Max('sort_order')"))
ok('drag-handle' not in BEFORE[TPL],
   'CONTROL: the planner had no grip of any kind')


# ==========================================================================
head('3. DRIVEN - THREE MEALS, DRAGGED')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
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
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

PAGE = None
if django_up:
    import datetime as dt
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Recipe

    editor = User.objects.create_user(username='ro1', password='x',
                                      email='ro1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        editor.user_permissions.add(Permission.objects.get(codename=cn))
    reader = User.objects.create_user(username='ro1r', password='x',
                                      email='ro1r@example.test')
    reader.user_permissions.add(
        Permission.objects.get(codename='can_access_recipes'))
    cl, ro = Client(), Client()
    cl.force_login(editor)
    ro.force_login(reader)

    DAY = dt.date(2026, 10, 21)
    URL = '/meal_plans/reorder/'

    soup = Recipe.objects.create(recipe_name='Soup for six', servings=6)
    stew = Recipe.objects.create(recipe_name="Yiayia's stew", servings=2)
    pie = Recipe.objects.create(recipe_name='Fish pie', servings=4)

    def mk(recipe, order, note=''):
        return MealEntry.objects.create(
            date=DAY, recipe=recipe, note=note, servings=4,
            sort_order=order, created_by=editor)

    def order_now():
        return list(MealEntry.objects.filter(date=DAY)
                    .order_by('sort_order', 'meal_entry_id')
                    .values_list('meal_entry_id', flat=True))

    a, b, c = mk(soup, 1), mk(stew, 2), mk(pie, 3)
    ok(order_now() == [a.meal_entry_id, b.meal_entry_id, c.meal_entry_id],
       'three meals on one day, in the order they were added',
       order_now())

    # ---- THE DRAG: last to first.
    want = [c.meal_entry_id, a.meal_entry_id, b.meal_entry_id]
    r = cl.post(URL, {'date': DAY.strftime('%Y-%m-%d'),
                      'order': ','.join(str(i) for i in want)})
    ok(r.status_code == 200, 'a reorder answers 200', r.status_code)
    body = json.loads(r.content.decode('utf-8')) if r.status_code == 200 \
        else {}
    ok(body.get('ok') is True, '  and says so', body)
    ok(order_now() == want,
       '  AND THE DAY IS IN THAT ORDER - read back out of the database, '
       'not out of the answer', order_now())
    ok(sorted(MealEntry.objects.filter(date=DAY)
              .values_list('sort_order', flat=True)) == [1, 2, 3],
       '  numbered 1, 2, 3 - no gaps left for the next writer to fall in',
       sorted(MealEntry.objects.filter(date=DAY)
              .values_list('sort_order', flat=True)))

    # ---- IT REFUSES RATHER THAN GUESSES.
    print('')
    stale = [c.meal_entry_id, a.meal_entry_id]          # b left out
    r = cl.post(URL, {'date': DAY.strftime('%Y-%m-%d'),
                      'order': ','.join(str(i) for i in stale)})
    ok(r.status_code == 409,
       'REFUSED: an order missing a row the day really has', r.status_code)
    if r.status_code == 409:
        said = json.loads(r.content.decode('utf-8'))
        ok(said.get('order') == order_now(),
           '  and the refusal carries the REAL order, so the page has '
           'something to put itself right with', said)
    ok(order_now() == want, '  and nothing was written', order_now())

    for data, why in (
            ({'date': DAY.strftime('%Y-%m-%d'),
              'order': '%d,%d' % (a.meal_entry_id, a.meal_entry_id)},
             'the same row twice'),
            ({'date': 'nope', 'order': str(a.meal_entry_id)},
             'a junk date'),
            ({'order': str(a.meal_entry_id)}, 'no date at all'),
            ({'date': DAY.strftime('%Y-%m-%d'), 'order': ''},
             'an empty order'),
            ({'date': DAY.strftime('%Y-%m-%d'), 'order': 'a,b,c'},
             'an order that is not numbers')):
        r = cl.post(URL, data)
        ok(r.status_code in (400, 409),
           'REFUSED: %s' % why, r.status_code)
    ok(order_now() == want,
       'and after five refusals the day is still as the drag left it',
       order_now())

    # ---- WHO MAY.
    print('')
    r = cl.get(URL)
    ok(r.status_code == 405, 'the route refuses a GET', r.status_code)
    r = ro.post(URL, {'date': DAY.strftime('%Y-%m-%d'),
                      'order': ','.join(str(i) for i in want)})
    ok(r.status_code == 403,
       'a reader without can_edit_recipes is refused', r.status_code)
    r = Client().post(URL, {'date': DAY.strftime('%Y-%m-%d'),
                            'order': '1'})
    ok(r.status_code in (302, 403),
       'and so is nobody at all', r.status_code)

    # ---- A LEFTOVER AND A NOTE DRAG LIKE ANYTHING ELSE.
    MealEntry.objects.all().delete()
    p1 = mk(soup, 1)
    lo = MealEntry.objects.create(date=DAY, recipe=soup, servings=4,
                                  sort_order=2, leftover_of=p1,
                                  created_by=editor)
    nt = mk(None, 3, note='Eat out')
    mix = [nt.meal_entry_id, lo.meal_entry_id, p1.meal_entry_id]
    r = cl.post(URL, {'date': DAY.strftime('%Y-%m-%d'),
                      'order': ','.join(str(i) for i in mix)})
    ok(r.status_code == 200 and order_now() == mix,
       'a note and a leftover drag like any other row - position is not '
       'what ties a leftover to its meal', order_now())
    lo.refresh_from_db()
    ok(lo.leftover_of_id == p1.meal_entry_id,
       '  and the leftover still knows what it came from even though it '
       'now sits ABOVE it', lo.leftover_of_id)

    # ---- AND THE PAGE ITSELF, for section 4.
    MealEntry.objects.all().delete()
    e1, e2, e3 = mk(soup, 1), mk(stew, 2), mk(pie, 3)
    DRAW = [e1.meal_entry_id, e2.meal_entry_id, e3.meal_entry_id]
    PAGE = cl.get('/meal_plans/planner/?view=day&date=%s'
                  % DAY.strftime('%Y-%m-%d')).content.decode('utf-8')


# ==========================================================================
head('4. RENDERED - THE GRIP, WITH THE LIBRARY AND WITHOUT IT')
# ==========================================================================
# THE DEGRADATION CLAIM IS ABOUT A BROWSER, so it is asked in one. The
# page is rendered twice against the SAME markup: once with Sortable
# 1.15.0 really served, once with the CDN failing. A stylesheet rule
# read out of the file would not have caught a script that added the
# class before checking.
# VS-1, 29 Oct 2026 - THE FILE THE APP SERVES, so this section runs on any
# machine with the repo; it used to read a sandbox-only path and skipped
# everywhere else.
LOCAL = os.path.join(ROOT, 'static', 'vendor', 'sortablejs', 'Sortable.min.js')
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

# AND THE WRAPPER MUST BE ON THE PAGE. Against the reverted tree there
# is no .day-rows at all, and every eval_on_selector below would RAISE
# rather than fail - a crash blocks a push exactly as hard as a failure
# and says far less about why. So it is a claim first, and the section
# is skipped when it does not hold.
HAS_ROWS = PAGE is not None and 'class="day-rows"' in PAGE
if PAGE is not None:
    ok(HAS_ROWS, 'the rendered page carries the row wrapper')
if not HAS_ROWS or sync_playwright is None or not os.path.isfile(LOCAL):
    skip('section 4', 'no row wrapper on the page, no Playwright, or no '
                      'local Sortable to serve')
else:
    FIX = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
    css = read(FIX) if os.path.isfile(FIX) else ''
    VEND = '/tmp/claude-0/drive/node_modules'
    FA = '/opt/npm-tools/node_modules/@fortawesome/fontawesome-free'
    posted = {}

    def router(serve_sortable):
        def route(r):
            url = r.request.url
            if '/meal_plans/reorder/' in url:
                posted['body'] = r.request.post_data or ''
                posted['method'] = r.request.method
                return r.fulfill(status=200, body=b'{"ok": true}',
                                 content_type='application/json')
            if 'Sortable' in url:
                if serve_sortable:
                    with open(LOCAL, 'rb') as f:
                        return r.fulfill(status=200, body=f.read(),
                                         content_type='application/javascript')
                # THE CDN FAILING, exactly as it would.
                return r.fulfill(status=504, body=b'')
            if ('font-awesome' in url or 'fontawesome' in url) \
                    and url.endswith('.css'):
                p = FA + '/css/all.min.css'
                if os.path.isfile(p):
                    with open(p, 'rb') as f:
                        return r.fulfill(status=200, body=f.read(),
                                         content_type='text/css')
            if 'bootstrap' in url and url.endswith('.css'):
                return r.fulfill(status=200, body=css.encode('utf-8'),
                                 content_type='text/css')
            for k, pth in (('jquery', VEND + '/jquery/dist/jquery.min.js'),
                           ('popper',
                            VEND + '/popper.js/dist/umd/popper.min.js'),
                           ('bootstrap.min.js',
                            VEND + '/bootstrap/dist/js/bootstrap.min.js')):
                if k in url and os.path.isfile(pth):
                    with open(pth, 'rb') as f:
                        return r.fulfill(
                            status=200, body=f.read(),
                            content_type='application/javascript')
            return r.fulfill(status=200, body=b'',
                             content_type='text/plain')
        return route

    html = PAGE.replace('<head>', '<head><base href="http://127.0.0.1/">')
    with sync_playwright() as pw:
        br = pw.chromium.launch()

        # ---- WITHOUT THE LIBRARY
        pg = br.new_page(viewport={'width': 1280, 'height': 1000})
        pg.route(re.compile(r'^https?://'), router(False))
        pg.set_content(html, wait_until='load')
        pg.wait_for_timeout(500)
        cls = pg.eval_on_selector('.day-rows', 'e => e.className')
        vis = pg.eval_on_selector(
            '.day-rows .drag-handle',
            'e => getComputedStyle(e).display')
        ok('is-draggable' not in cls,
           'WITH THE CDN FAILING the row list is NOT marked draggable',
           cls)
        ok(vis == 'none',
           '  and the grip is not drawn at all - no dead control on the '
           'card', vis)
        pg.close()

        # ---- WITH IT
        pg = br.new_page(viewport={'width': 1280, 'height': 1000})
        pg.route(re.compile(r'^https?://'), router(True))
        pg.set_content(html, wait_until='load')
        pg.wait_for_timeout(600)
        cls = pg.eval_on_selector('.day-rows', 'e => e.className')
        box = pg.eval_on_selector(
            '.day-rows .drag-handle',
            'e => { var r = e.getBoundingClientRect();'
            ' return [getComputedStyle(e).display, r.width, r.height]; }')
        ok('is-draggable' in cls,
           'WITH SORTABLE SERVED the row list is marked draggable', cls)
        ok(box[0] != 'none' and box[1] > 0,
           '  and the grip is drawn - %s, %.0fx%.0f'
           % (box[0], box[1], box[2]), box)
        ok(box[2] >= 24,
           '  and it is at least 24px tall at desktop width - %.0f'
           % box[2], box[2])

        pg.close()

        # ---- AND IT STILL FITS ON A PHONE. The grip takes 44px of a
        # 286px row and the first draft of this round pushed the fourth
        # action button off the edge of the card. Nothing in a
        # stylesheet would have said so; the renders did. This measures
        # it, so the next round that adds a control to this row finds
        # out here instead.
        pg = br.new_page(viewport={'width': 390, 'height': 1400})
        pg.route(re.compile(r'^https?://'), router(True))
        pg.set_content(html, wait_until='load')
        pg.wait_for_timeout(600)
        fit = pg.evaluate("""() => {
            const card = document.querySelector('.day-card');
            const cb = card.getBoundingClientRect();
            let worst = 0, n = 0, small = 0;
            document.querySelectorAll('.day-rows .recipe-item')
                .forEach(row => {
                    row.querySelectorAll('.row-actions > *').forEach(b => {
                        const r = b.getBoundingClientRect();
                        n += 1;
                        worst = Math.max(worst, r.right - cb.right);
                        if (Math.min(r.width, r.height) < 36) { small += 1; }
                    });
                    const g = row.querySelector('.drag-handle');
                    if (g) {
                        const r = g.getBoundingClientRect();
                        if (Math.max(r.width, r.height) < 44) { small += 1; }
                    }
                });
            return [n, worst, small,
                    document.documentElement.scrollWidth];
        }""")
        ok(fit[1] <= 0,
           'AT 390px every action button is INSIDE the card - worst '
           'overhang %.0fpx across %d of them' % (fit[1], fit[0]), fit)
        ok(fit[2] == 0,
           '  and nothing was shrunk below a thumb to make room', fit[2])
        ok(fit[3] <= 390,
           '  and the page does not scroll sideways - %dpx' % fit[3],
           fit[3])
        pg.close()

        # ---- A REAL DRAG, AND THE REQUEST IT SENDS.
        pg = br.new_page(viewport={'width': 1280, 'height': 1000})
        pg.route(re.compile(r'^https?://'), router(True))
        pg.set_content(html, wait_until='load')
        pg.wait_for_timeout(600)
        rows = pg.eval_on_selector_all(
            '.day-rows [data-entry]', 'es => es.map(e => e.dataset.entry)')
        ok(len(rows) == 3, 'three rows on the rendered day', rows)
        h = pg.query_selector_all('.day-rows .drag-handle')
        if len(h) >= 3 and len(rows) == 3:
            src = h[2].bounding_box()
            dst = h[0].bounding_box()
            pg.mouse.move(src['x'] + src['width'] / 2,
                          src['y'] + src['height'] / 2)
            pg.mouse.down()
            for i in range(1, 11):
                pg.mouse.move(
                    dst['x'] + dst['width'] / 2,
                    src['y'] + (dst['y'] - src['y']) * i / 10.0
                    - (6 if i == 10 else 0))
                pg.wait_for_timeout(25)
            pg.mouse.up()
            pg.wait_for_timeout(700)
            after = pg.eval_on_selector_all(
                '.day-rows [data-entry]',
                'es => es.map(e => e.dataset.entry)')
            moved = ok(after != rows,
                       'DRAGGING THE LAST ROW TO THE TOP really moves it '
                       'on screen: %r -> %r' % (rows, after), after)
            ok(posted.get('method') == 'POST',
               '  and the drop POSTS', posted.get('method'))
            # IT IS A FormData POST, so the body is multipart and
            # not a query string. Read the parts rather than guessing
            # at a shape the browser chose.
            sent = posted.get('body', '')
            parts = dict(
                (m.group(1), m.group(2).strip())
                for m in re.finditer(
                    r'name="([^"]+)"\r?\n\r?\n(.*?)\r?\n--',
                    sent, re.S))
            ok(set(parts) >= {'date', 'order', 'csrfmiddlewaretoken'},
               '  carrying the order, the day and a CSRF token',
               sorted(parts))
            ok(parts.get('date') == '2026-10-21',
               '  and the day it is about - %r' % parts.get('date'))
            if moved:
                got = parts.get('order', '').split(',')
                ok(got == after,
                   '  and what it sent is what is ON THE SCREEN - %r'
                   % (got,), (got, after))
        else:
            skip('the real drag', 'the grips were not all drawn')
        pg.close()
        br.close()


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
# NO MIGRATION, AND NOTHING TAKEN AWAY. sort_order has been on the
# model since MN-1; this round is an endpoint, a wrapper and a grip.
ok(not os.path.isfile(os.path.join(ROOT, 'pages', 'models.py') + SUFFIX),
   'NO MIGRATION and no model change - sort_order was already there and '
   'already meant this')

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
ok('def reorder_meal_day' in gate and 'day-rows' in gate,
   'both sentinels are on the push gate')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_day_order as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that the WEEK view can be dragged - WD-1 does that, on')
print('  22 October, through this round endpoint, and test_week_drag')
print('  is where it is proved. What this round proves is the Day')
print('  card, which is what Demetri asked about first.')
print('')
print('  Not that two people dragging the same day at once end up')
print('  agreeing. The second one is refused with the real order and')
print('  the page reloads, which is honest rather than clever.')
print('')
print('  Not that the CDN is reliable. It is measured failing in')
print('  section 4, and what that costs is the grip and nothing')
print('  else - Move, Remove and Leftovers are untouched.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
