# -*- coding: utf-8 -*-
"""test_week_drag.py - round WD-1, 22 Oct 2026.

THE WEEK'S SEVEN COLUMNS DRAG INTO ORDER NOW.

RO-1 shipped drag-to-reorder on the Day card on 21 October and left the
Week view alone, with the question put to Demetri. He answered on 22
October: yes, add it. This is that.

NO NEW ENDPOINT, AND SECTION 1 ASKS FOR THAT RATHER THAN FOR CODE.
reorder_meal_day has taken a date and an order since RO-1, and refuses
an order that is not exactly the rows on that date. A week column IS a
date. The claim this round makes is therefore a negative one as much as
a positive one: the week drags, AND the module gained no second way to
write an order.

WITHIN A COLUMN ONLY, AND THAT IS A DESIGN AND NOT A SHORTFALL. Each
column is its own Sortable with no shared group. Dragging a chip from
Tuesday to Wednesday writes a DATE, not an order, and that is Move on
the chip menu - which travels leftovers with their meal, which an order
write would not. One gesture that silently did either depending on
where the pointer landed is how a plan gets quietly rearranged. Section
1 refuses a shared group by reading the binding, and section 4 proves
in a browser that a chip dragged at a neighbouring column does not land
there.

THE CHIP IS THE HANDLE. A day row carries a thumbnail, a stepper and
four icon buttons, so a drag there needs a grip of its own. A week
column is 152px at 1200px - MV-3 measured it and refused to put a
stepper or row actions in one for that reason - and a chip in it has a
single interaction. There is no room for a grip and nothing for one to
disambiguate.

AND ON A PHONE THERE IS NOTHING TO DRAG, WHICH IS MV-3's DESIGN. Below
768px .week-grid is display:none and .day-strip takes over - seven
buttons and the Day card beneath them - so the phone's reorder gesture
is RO-1's grip on that card, measured at 390px by test_day_order.
Section 4 asks a 390px Chromium for the grid's computed display rather
than for a chip's height, because the first draft of it asked for chip
heights, got four chips of ZERO height, and was one step from being
written off as a layout bug.

A DROP IS NOT A CLICK, AND THAT COST A GUARD IN SOMEBODY ELSE'S CODE.
RD-2's chip menu opens from a CAPTURING listener on the document, the
only place one delegated handler can get in front of the inline onclick
further down the tree. Without a guard every drop opened the menu of
whatever was dropped, and a drop on the column body opened the picker.
The listener now returns early if a drag ended within the last 300ms,
cleared by time rather than by the next click - a drop that lands
outside any chip produces no click at all, and a flag cleared by a
click that never comes stays set for ever. Section 4 drops a chip and
then asks whether a menu opened.

A FLAW THAT WAS MEASURED AND TURNED OUT NOT TO EXIST. reorder_meal_day
is edit-tier, so the first draft of this round added a permission flag
to both bindings: a view-only member who could grip a meal, drag the
day into a new order and watch the page reload it back would be looking
at a control that lies. Then the template was asked rather than
assumed, and both bindings already sit inside the
{% if perms.auth.can_edit_recipes %} block that opens above openPicker.
The flag was a second lock on a locked door and it was taken out.
Section 1 asks instead that the block really does enclose the new
binding, and section 3 renders the week as a reader: the chips are
there and the script is not. Nothing pinned that before.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The column carries its date; the chips drag; no
      shared group; no second endpoint; the binding is inside the
      edit-tier block; the guide promises what is really left.

  2   THE CONTROL. Re-asked of .bak_weekdrag, where the column had no
      date on it and nothing in the week could be dragged at all.

  3   DRIVEN. A week of meals through RO-1's endpoint with a week
      column's date and a week column's ids; an order carrying another
      day's meal refused; the reader's render, chips and no script.

  4   RENDERED. Chromium, four times: the CDN failing, the CDN served,
      a real mouse drag in a column - the POST read back, the
      neighbouring columns counted, and neither the chip menu nor the
      picker opened by the drop - and a phone, where the grid is not
      drawn at all.

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
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_weekdrag'
ME = 'test_week_drag.py'
PATCHER = 'apply_week_drag.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'WD-1, 22 Oct 2026'
# VS-1, 29 Oct 2026 - the library is served from the app now, not the CDN.
SORTABLE = "{% static 'vendor/sortablejs/Sortable.min.js' %}"

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
GUIDE = os.path.join(ROOT, 'pages', 'help_content', 'administration.html')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL, GUIDE)

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


# THE BINDING IS READ AS A SLICE, NOT AS A WHOLE FILE. This page holds
# two Sortables now - RO-1's on .day-rows and this round's on the
# columns - and a claim about "the binding" that searched the whole
# script would be satisfied by either one. .find(), not .index():
# against the reverted tree the column binding is not there at all and
# .index() would RAISE, which blocks a push exactly as hard as a
# failure and says far less about why.
def column_binding(js):
    a = js.find("document.querySelectorAll('.week-col-body[data-day]')")
    b = js.find('function saveColumnOrder')
    if not 0 <= a < b:
        return ''
    # AND IT STARTS AT THE IIFE, NOT AT THE QUERY, because the library
    # guard is the FIRST line inside it and a slice that began at the
    # query would have cut the guard off and then asked whether it was
    # there. rfind back to the opening, which is the day card binding
    # closing brace away and cannot be confused with it.
    o = js.rfind('(function () {', 0, a)
    return js[o if o >= 0 else a:b]


def save_column(js):
    a = js.find('function saveColumnOrder')
    b = js.find('function saveDayOrder')
    return js[a:b] if 0 <= a < b else ''


def claims(d):
    t = d[TPL]
    js = T.code_only_js(t)
    col = column_binding(js)
    sav = save_column(js)
    g = d[GUIDE]
    return {
        # NOT "data-day is somewhere in the file". It was: the DAY card
        # has carried one since RO-1, so the bare string held before
        # this round and the control section said so. The claim is that
        # the COLUMN carries one, which is a different sentence.
        'the week column carries its own date':
            bool(re.search(
                r'class="week-col-body"\s*\n\s*'
                r'data-day="\{\{ day\.date\|date:\'Y-m-d\'\}?\}?', t)),
        '  and one Sortable is bound per column':
            bool(col) and 'new Sortable(col' in col,
        '  dragging the chips themselves, with no grip in a 152px column':
            "draggable: '.week-chip'" in col,
        '  and NOT across days - no shared group':
            bool(col) and 'group' not in col,
        '  with the same four class names the rest of the app drags with':
            ("ghostClass: 'sortable-ghost'" in col
             and "dragClass: 'sortable-drag'" in col
             and "chosenClass: 'sortable-chosen'" in col
             and 'animation: 150' in col),
        '  and nothing is marked draggable until Sortable answers':
            bool(col) and "typeof Sortable === 'undefined'" in col,
        'the drop sends the ids and the day to RO-1 endpoint':
            ('function saveColumnOrder' in js
             and "{% url \"reorder_meal_day\" %}" in t
             and "col.getAttribute('data-day')" in js),
        # ASKED OF saveColumnOrder, not of the file. RO-1 handles 409
        # in saveDayOrder, so the bare string held before this round.
        '  and a 409 reloads rather than guessing':
            bool(sav) and 'r.status === 409' in sav,
        'a drop is not a click - the capturing listener returns early':
            ('window.__alvDragEnded' in js
             and 'Date.now() - window.__alvDragEnded < 300' in js),
        '  and the flag is cleared when a drag STARTS, not by a click':
            'onStart: function () { window.__alvDragEnded = 0; }' in col,
        'the stylesheet dresses a chip being dragged':
            '.week-col-body.is-draggable .week-chip { cursor: grab;' in t,
        # A RING, NOT A FILL. The first draft copied RO-1 and set the
        # chosen background to accent-soft, which is what a normal
        # week chip ALREADY IS - dE 0.0 in CIE Lab, an invisible
        # state, caught by the renders and not by any claim. A fill
        # cannot win here because the fill carries meaning: three
        # chip types, three colours. See the rule's own comment.
        '  and marks the chosen one with a ring rather than a fill':
            ('.week-col-body .sortable-chosen {\n'
             '    box-shadow: 0 0 0 2px var(--alv-accent-ink);' in t),
        'the guide says the week drags':
            'the meals themselves drag up and down their own column' in g,
        '  and names crossing days as what is still coming':
            'dragging a meal from one day to another' in g,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# THE VIEW MODULE IS NOT IN FILES, and that is the claim. This round
# backed up ten files and the endpoint module is not one of them, so it
# is read fresh rather than out of NOW.
V = T.python_code_only(read(VIEW), payloads=True)
JS = T.code_only_js(NOW[TPL])
COL = column_binding(JS)

# THE POINT OF THIS ROUND IS THAT IT ADDED NO ENDPOINT. So that is a
# claim, and it is counted rather than searched: one function that
# writes an order, and it is RO-1's.
ok('def reorder_meal_day' in V,
   'the endpoint it posts to is RO-1 and is still there')
ok(len(re.findall(r'^def reorder', V, re.M)) == 1,
   'and it is the ONLY reorder endpoint in the module - a column is a '
   'date, so there was nothing to add',
   re.findall(r'^def reorder', V, re.M))
ok(not os.path.isfile(VIEW + SUFFIX),
   '  which is why the view module is not even backed up by this round')
ok(not os.path.isfile(os.path.join(ROOT, 'pages', 'urls.py') + SUFFIX),
   '  and neither is urls.py - no route was added either')

# MOVE IS STILL THERE, AND IT IS WHAT CROSSING DAYS MEANS.
ok('def move_meal_entry' in V,
   'GUARD: moving a meal to another day is STILL its own endpoint - a '
   'date write, which is not an order write')
ok('data-move=' in NOW[TPL] and 'askMove(' in JS,
   '  and still its own control on the chip menu, which is why the '
   'drag deliberately cannot cross columns')

# TWO BINDINGS, TWO GUARDS, ONE FLAG.
ok(JS.count("typeof Sortable === 'undefined'") == 2,
   'both bindings on this page guard on the library - the day card and '
   'the week columns', JS.count("typeof Sortable === 'undefined'"))

# WHO MAY DRAG, ASKED OF THE TEMPLATE AND NOT ASSUMED. The first draft
# of this round added a permission flag to both bindings, because
# reorder_meal_day is edit-tier and a view-only member dragging a day
# into order only to watch it reload would be a control that lies. Then
# it was measured: the whole script region sits inside the
# {% if perms.auth.can_edit_recipes %} block that opens above
# openPicker. The flag was a second lock on a locked door, and it was
# taken out. What is asked instead is that the block really encloses
# the new binding - nothing pinned that before, and a later round that
# moved the script would take the lock with it.
_at = NOW[TPL].find(
    "document.querySelectorAll('.week-col-body[data-day]')")
_enc = []
if _at > 0:
    for _m in re.finditer(r'\{%\s*(if|endif)\b([^%]*)%\}', NOW[TPL][:_at]):
        if _m.group(1) == 'if':
            _enc.append(_m.group(2).strip())
        elif _enc:
            _enc.pop()
ok('perms.auth.can_edit_recipes' in _enc,
   'the week binding is INSIDE the edit-tier block, so a reader is '
   'served the chips and no drag at all', _enc)
ok('ALV_MAY_ORDER' not in NOW[TPL],
   '  and this round added no second lock for it - the flag the first '
   'draft wrote was measured, found redundant and removed')

# THE COLUMN BINDING SKIPS AN EMPTY COLUMN. A week with a day off has
# a column holding one em dash and no chips, and Sortable on it would
# accept a drop that saveColumnOrder then refuses to send.
# AND THE THREE CHIP COLOURS SURVIVE THE DRAG. They are what says
# whether a meal is a meal, a note or a leftover, and a chosen-state
# fill would take that away from whichever one is being moved.
ok('.week-col-body .sortable-chosen { background' not in NOW[TPL],
   'the chosen chip keeps its own fill - the colour says what KIND of '
   'meal it is, and that is not the drag to borrow')
ok('.week-chip.is-note' in NOW[TPL] and '.week-chip.is-leftover'
   in NOW[TPL],
   '  and all three kinds are still coloured - meal, note, leftover')

ok("if (!col.querySelector('.week-chip')) { return; }" in COL,
   'an empty column is not bound at all - there is nothing in it to '
   'put in an order')

# AND THE TAGS STILL BALANCE. BM-1's lesson, 22 October: a template
# that is wrong in a way no suite reads prints across every page.
ok(NOW[TPL].count('{%') == NOW[TPL].count('%}'),
   'the template tags balance - %d {%% against %d %%}'
   % (NOW[TPL].count('{%'), NOW[TPL].count('%}')))
bad = [i + 1 for i, ln in enumerate(NOW[TPL].split('\n'))
       if ln.count('{#') != ln.count('#}')]
ok(not bad,
   'and no Django comment is left open across a line break - BM-1 '
   'printed one across 136 pages on 22 October', bad[:6])


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

oldjs = T.code_only_js(BEFORE[TPL])
ok('class="week-col-body"' in BEFORE[TPL],
   'CONTROL: the week column was already there - MV-3 built it')
ok('data-day=' in BEFORE[TPL],
   'CONTROL: and data-day was already a thing this page used, on the '
   'day card - the column simply did not carry one')
ok("querySelector('.day-rows')" in oldjs,
   'CONTROL: the DAY card could already be dragged - RO-1, 21 October')
ok('week-col-body[data-day]' not in oldjs,
   'CONTROL: and the week could not, at all')
ok('perms.auth.can_edit_recipes' in BEFORE[TPL],
   'CONTROL: and the edit-tier block that guards the binding was '
   'already there - this round put the week binding INSIDE it rather '
   'than adding a lock of its own')
ok('reordering the week view' in BEFORE[GUIDE],
   'CONTROL: the guide named the week as the thing still coming')


# ==========================================================================
head('3. DRIVEN - A WEEK COLUMN IS A DATE')
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
DAYS = []
if django_up:
    import datetime as dt
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Recipe

    editor = User.objects.create_user(username='wd1', password='x',
                                      email='wd1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        editor.user_permissions.add(Permission.objects.get(codename=cn))
    reader = User.objects.create_user(username='wd1r', password='x',
                                      email='wd1r@example.test')
    reader.user_permissions.add(
        Permission.objects.get(codename='can_access_recipes'))
    cl, ro = Client(), Client()
    cl.force_login(editor)
    ro.force_login(reader)

    # WEDNESDAY 21 OCTOBER 2026, in a week that starts on the Monday.
    WED = dt.date(2026, 10, 21)
    THU = dt.date(2026, 10, 22)
    URL = '/meal_plans/reorder/'

    soup = Recipe.objects.create(recipe_name='Soup for six', servings=6)
    stew = Recipe.objects.create(recipe_name="Yiayia's stew", servings=2)
    pie = Recipe.objects.create(recipe_name='Fish pie', servings=4)

    def mk(day, recipe, order, note=''):
        return MealEntry.objects.create(
            date=day, recipe=recipe, note=note, servings=4,
            sort_order=order, created_by=editor)

    def order_on(day):
        return list(MealEntry.objects.filter(date=day)
                    .order_by('sort_order', 'meal_entry_id')
                    .values_list('meal_entry_id', flat=True))

    w1, w2, w3 = mk(WED, soup, 1), mk(WED, stew, 2), mk(WED, pie, 3)
    t1 = mk(THU, pie, 1)

    # ---- WHAT A COLUMN SENDS IS WHAT A CARD SENDS.
    want = [w3.meal_entry_id, w1.meal_entry_id, w2.meal_entry_id]
    r = cl.post(URL, {'date': WED.strftime('%Y-%m-%d'),
                      'order': ','.join(str(i) for i in want)})
    ok(r.status_code == 200 and order_on(WED) == want,
       'a column date and a column ids reorder that day - the endpoint '
       'cannot tell which view sent them, and does not need to',
       (r.status_code, order_on(WED)))
    ok(order_on(THU) == [t1.meal_entry_id],
       '  and Thursday is untouched, because an order is about one date',
       order_on(THU))

    # ---- AND THE THING THE DRAG DELIBERATELY CANNOT DO IS REFUSED
    #      ANYWAY, which is why no shared group is a design and not a
    #      promise. An order that names a row from another day is not
    #      a move; it is a lie about what is on the date.
    cross = [w3.meal_entry_id, w1.meal_entry_id, w2.meal_entry_id,
             t1.meal_entry_id]
    r = cl.post(URL, {'date': WED.strftime('%Y-%m-%d'),
                      'order': ','.join(str(i) for i in cross)})
    ok(r.status_code in (400, 409),
       'REFUSED: an order carrying Thursday meal in Wednesday column - '
       'crossing days is a DATE write and this endpoint does not do '
       'dates', r.status_code)
    ok(order_on(WED) == want and order_on(THU) == [t1.meal_entry_id],
       '  and neither day moved', (order_on(WED), order_on(THU)))

    # ---- THE READER.
    r = ro.post(URL, {'date': WED.strftime('%Y-%m-%d'),
                      'order': ','.join(str(i) for i in want)})
    ok(r.status_code == 403,
       'a reader without can_edit_recipes is refused by the endpoint',
       r.status_code)

    WEEKURL = ('/meal_plans/planner/?view=week&date=%s'
               % WED.strftime('%Y-%m-%d'))
    # AND THE READER'S PAGE IS WHERE THE PERMISSION CLAIM IS REALLY
    # SETTLED. Not a flag in the script - the script is not there. This
    # is the measurement that made the first draft's flag unnecessary,
    # and it is a claim rather than a note because nothing else in the
    # tree asks it.
    rp = ro.get(WEEKURL).content.decode('utf-8')
    ok('week-col-body' in rp and 'week-chip' in rp,
       '  a reader is served the week, chips and all')
    ok("querySelectorAll('.week-col-body[data-day]')" not in rp,
       '  AND NOT THE BINDING - the whole script region is inside the '
       'edit-tier block, so there is no grab cursor and no drag that '
       'reloads itself away')
    ok('new Sortable' not in rp,
       '  nor the day card binding either, which is RO-1 and was '
       'already inside the same block')

    PAGE = cl.get(WEEKURL).content.decode('utf-8')
    ok("querySelectorAll('.week-col-body[data-day]')" in PAGE,
       'and an editor IS served the binding')
    DAYS = re.findall(r'class="week-col-body"\s*\n\s*data-day="([^"]+)"',
                      PAGE)
    ok(len(DAYS) == 7,
       'the rendered week has seven columns, each carrying its date',
       DAYS)
    ok(WED.strftime('%Y-%m-%d') in DAYS,
       '  including the one the three meals are on', DAYS)


# ==========================================================================
head('4. RENDERED - A REAL DRAG IN A REAL COLUMN')
# ==========================================================================
# VS-1, 29 Oct 2026 - THE FILE THE APP SERVES, so this section runs on any
# machine with the repo; it used to read a sandbox-only path and skipped
# everywhere else.
LOCAL = os.path.join(ROOT, 'static', 'vendor', 'sortablejs', 'Sortable.min.js')
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

# THE COLUMN MUST BE ON THE PAGE FIRST. Against the reverted tree
# there is no .week-col-body[data-day] and every eval_on_selector
# below would RAISE rather than fail.
# AND IT IS DAYS, NOT A SUBSTRING. The reverted page still holds
# class="week-col-body" and still holds data-day= - on the DAY card -
# so a conjunction of the two was satisfied and section 4 then raised
# on the first selector. DAYS is built by the regex that insists the
# two are the same element, and the one date the chips are on must be
# among them.
HAS_COL = PAGE is not None and '2026-10-21' in DAYS
if PAGE is not None:
    ok(HAS_COL, 'the rendered week carries a column with a date on it')
if not HAS_COL or sync_playwright is None or not os.path.isfile(LOCAL):
    skip('section 4', 'no dated column on the page, no Playwright, or '
                      'no local Sortable to serve')
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
                        return r.fulfill(
                            status=200, body=f.read(),
                            content_type='application/javascript')
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
    FULL = '.week-col-body[data-day="%s"]' % '2026-10-21'
    with sync_playwright() as pw:
        br = pw.chromium.launch()

        # ---- WITHOUT THE LIBRARY. A chip that looks draggable and is
        #      not is worse than a chip that does not.
        pg = br.new_page(viewport={'width': 1280, 'height': 1000})
        pg.route(re.compile(r'^https?://'), router(False))
        pg.set_content(html, wait_until='load')
        pg.wait_for_timeout(500)
        cls = pg.eval_on_selector(FULL, 'e => e.className')
        cur = pg.eval_on_selector(
            FULL + ' .week-chip', 'e => getComputedStyle(e).cursor')
        ok('is-draggable' not in cls,
           'WITH THE CDN FAILING no column is marked draggable', cls)
        ok(cur != 'grab',
           '  and a chip does not offer a grab cursor it cannot honour '
           '- %s' % cur, cur)
        pg.close()

        # ---- WITH IT.
        pg = br.new_page(viewport={'width': 1280, 'height': 1000})
        pg.route(re.compile(r'^https?://'), router(True))
        pg.set_content(html, wait_until='load')
        pg.wait_for_timeout(600)
        cls = pg.eval_on_selector(FULL, 'e => e.className')
        cur = pg.eval_on_selector(
            FULL + ' .week-chip', 'e => getComputedStyle(e).cursor')
        ok('is-draggable' in cls,
           'WITH SORTABLE SERVED the column is marked draggable', cls)
        ok(cur == 'grab', '  and the chip offers a grab cursor - %s' % cur)
        empty = pg.evaluate("""() => {
            let n = 0;
            document.querySelectorAll('.week-col-body[data-day]')
                .forEach(c => {
                    if (!c.querySelector('.week-chip')
                        && c.classList.contains('is-draggable')) { n += 1; }
                });
            return n;
        }""")
        ok(empty == 0,
           '  and a column with no meals in it was not bound at all',
           empty)
        pg.close()

        # ---- A REAL DRAG, AND THE REQUEST IT SENDS.
        pg = br.new_page(viewport={'width': 1280, 'height': 1000})
        pg.route(re.compile(r'^https?://'), router(True))
        pg.set_content(html, wait_until='load')
        pg.wait_for_timeout(600)
        chips = pg.eval_on_selector_all(
            FULL + ' [data-chip]', 'es => es.map(e => e.dataset.chip)')
        ok(len(chips) == 3, 'three chips in the Wednesday column', chips)
        els = pg.query_selector_all(FULL + ' .week-chip')
        if len(els) == 3:
            src = els[2].bounding_box()
            dst = els[0].bounding_box()
            pg.mouse.move(src['x'] + src['width'] / 2,
                          src['y'] + src['height'] / 2)
            pg.mouse.down()
            for i in range(1, 11):
                pg.mouse.move(
                    src['x'] + src['width'] / 2,
                    src['y'] + (dst['y'] - src['y']) * i / 10.0
                    - (6 if i == 10 else 0))
                pg.wait_for_timeout(25)
            pg.mouse.up()
            pg.wait_for_timeout(700)
            after = pg.eval_on_selector_all(
                FULL + ' [data-chip]', 'es => es.map(e => e.dataset.chip)')
            moved = ok(after != chips,
                       'DRAGGING THE LAST CHIP TO THE TOP really moves it '
                       'on screen: %r -> %r' % (chips, after), after)
            ok(posted.get('method') == 'POST',
               '  and the drop POSTS', posted.get('method'))
            sent = posted.get('body', '')
            parts = dict(
                (m.group(1), m.group(2).strip())
                for m in re.finditer(
                    r'name="([^"]+)"\r?\n\r?\n(.*?)\r?\n--', sent, re.S))
            ok(set(parts) >= {'date', 'order', 'csrfmiddlewaretoken'},
               '  carrying the order, the day and a CSRF token',
               sorted(parts))
            ok(parts.get('date') == '2026-10-21',
               '  and THE COLUMN DATE, read off the column rather than '
               'off the page - %r' % parts.get('date'))
            if moved:
                got = parts.get('order', '').split(',')
                ok(got == after,
                   '  and what it sent is what is ON THE SCREEN - %r'
                   % (got,), (got, after))

            # ---- THE DROP DID NOT OPEN A MENU. This is the whole
            #      reason RD-2's listener needed a guard: it captures,
            #      so without one every drop opened the menu of
            #      whatever was dropped.
            menu = pg.evaluate("""() => {
                const m = document.querySelector('#chipMenu, .chip-menu,'
                    + ' [data-chip-menu]');
                if (!m) { return 'no menu element on the page'; }
                const s = getComputedStyle(m);
                return (m.hidden || s.display === 'none'
                        || s.visibility === 'hidden') ? 'closed' : 'OPEN';
            }""")
            ok(menu == 'closed',
               '  AND THE DROP OPENED NO MENU - %s' % menu, menu)

            # ---- NOR DID IT OPEN THE PICKER, which the column body
            #      itself would have done through its inline onclick.
            pick = pg.evaluate("""() => {
                const m = document.querySelector('#pickerModal');
                if (!m) { return 'no picker element on the page'; }
                return m.classList.contains('show') ? 'OPEN' : 'closed';
            }""")
            ok(pick == 'closed',
               '  and no picker either, though the column body carries '
               'an onclick that opens one - %s' % pick, pick)

            # ---- AND NOTHING LANDED IN THE NEIGHBOURING COLUMN. No
            #      shared group, measured rather than asserted.
            others = pg.evaluate("""(wed) => {
                const out = {};
                document.querySelectorAll('.week-col-body[data-day]')
                    .forEach(c => {
                        const d = c.getAttribute('data-day');
                        if (d !== wed) {
                            out[d] = c.querySelectorAll('[data-chip]')
                                .length;
                        }
                    });
                return out;
            }""", '2026-10-21')
            ok(others.get('2026-10-22') == 1,
               '  and Thursday still holds its one meal and no more - '
               'nothing crossed columns', others)
            ok(sum(others.values()) == 1,
               '  nor did anything land in the other five days',
               others)
        else:
            skip('the real drag', 'the three chips were not all drawn')
        pg.close()

        # ---- AND ON A PHONE THERE IS NO WEEK GRID TO DRAG, which is
        #      MV-3's design and not this round's omission. At 767px
        #      and below .week-grid is display:none and .day-strip
        #      takes over: seven buttons and the Day card beneath
        #      them. So the phone's reorder gesture is RO-1's grip on
        #      that card, measured at 390px by test_day_order, and
        #      this round adds nothing a thumb can reach.
        #
        #      MEASURED RATHER THAN STATED, because the first draft of
        #      this section asked a 390px viewport for chip heights,
        #      got four chips of ZERO height, and was about to be
        #      written off as a layout bug. It is a hidden grid.
        pg = br.new_page(viewport={'width': 390, 'height': 1400})
        pg.route(re.compile(r'^https?://'), router(True))
        pg.set_content(html, wait_until='load')
        pg.wait_for_timeout(600)
        phone = pg.evaluate("""() => {
            const g = document.querySelector('.week-grid');
            const s = document.querySelector('.day-strip');
            return [g ? getComputedStyle(g).display : 'no grid',
                    s ? getComputedStyle(s).display : 'no strip',
                    document.querySelectorAll('.day-strip-btn').length,
                    document.documentElement.scrollWidth];
        }""")
        ok(phone[0] == 'none',
           'AT 390px the week GRID is not drawn at all - %s - so there '
           'is nothing to drag and nothing that looks draggable'
           % phone[0], phone)
        ok(phone[1] == 'grid' and phone[2] == 7,
           '  MV-3 day strip takes its place - %s, %d buttons - and the '
           'reorder gesture on a phone is RO-1 grip on the Day card'
           % (phone[1], phone[2]), phone)
        ok(phone[3] <= 390,
           '  and the page does not scroll sideways - %dpx' % phone[3],
           phone[3])
        pg.close()
        br.close()


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
# NOTHING WAS ADDED TO THE DATABASE OR TO THE ROUTES. sort_order has
# been on the model since MN-1 and the endpoint since RO-1.
for leaf in ('pages/models.py', 'pages/urls.py',
             'pages/views/recipes/meal_planning.py'):
    ok(not os.path.isfile(os.path.join(ROOT, *leaf.split('/')) + SUFFIX),
       'NO change to %s - this round is markup, a rule and a binding'
       % leaf)

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
ok('saveColumnOrder' in gate, 'the sentinel is on the push gate')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_week_drag as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')

# THE SUITES THAT HELD THE OLD PROMISE MOVED WITH IT.
for leaf in ('test_meal_guide3.py', 'test_meal_guide5.py',
             'test_meal_help.py', 'test_day_order.py'):
    txt = read(os.path.join(ROOT, leaf))
    ok('reordering the week view' not in txt,
       '%s no longer names the week as coming' % leaf)


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that a meal can be dragged from one day to another. It')
print('  cannot, on purpose: that writes a DATE and not an order, it')
print('  has to carry leftovers with it, and Move on the chip menu')
print('  already does both. The guide names it as what is coming.')
print('')
print('  Not that two people dragging the same day at once agree.')
print('  The second is refused with the real order and the page')
print('  reloads - RO-1 answer, and a column inherits it.')
print('')
print('  Not that a column can be dragged on a phone. It cannot: the')
print('  week grid is display:none below 768px by MV-3 design, and')
print('  the phone gesture is RO-1 grip on the Day card. Section 4')
print('  measures the hidden grid so that stays a decision.')
print('')
print('  Not that a touch drag on a tablet feels right. touch-action')
print('  is set and the chip is a 11px pill in a 152px column, but a')
print('  finger on real glass is Demetri testing, not Chromium.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
