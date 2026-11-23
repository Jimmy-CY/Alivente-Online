# -*- coding: utf-8 -*-
"""test_ra16_meal_send_drag.py - round RA16, 23 Nov 2026.

RELEASE RA16 - THE MEAL PLANNER: A LOOK BEFORE YOU ADD, A MEAL DRAGGED TO
ANOTHER DAY, AND THE PLAN SENT.
Demetri, 23 Nov: (1) an eye at the top right of each recipe in the Add a
meal picker that opens just the quick view; (2) drag a meal to another day
instead of Move to... (which stays); (3) a Share button - email, WhatsApp
- for the month, week and day: the day like the Day view, the week as
"Mon (23rd Nov): Chicken Kritharaki" with a day's other meals lined up
under its first, the month as a calendar. Called Send: Share is MS-1's.
No network: the email goes to Django's test outbox, the browser is fed
from the test client.
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

import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra16'
ME = 'test_ra16_meal_send_drag.py'
PATCHER = 'apply_ra16_meal_send_drag.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
PG = J(ROOT, 'pages')
TPL = J(PG, 'templates', 'meal_planner.html')
VIEW = J(PG, 'views', 'recipes', 'meal_planning.py')
SEND = J(PG, 'views', 'recipes', 'meal_send.py')
GUIDE = J(PG, 'help_content', 'administration.html')

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
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])


def claims(t, v):
    return {
        'SEND: a Send button on the bar, beside Print':
            'data-target="#sendModal" onclick="sendLoad()"' in t
            and '<i class="fas fa-paper-plane"></i> Send&hellip;' in t,
        '  and in the phone More menu': 'Send this plan...' in t,
        '  its dialog: the text, WhatsApp, Copy, the phone share, email':
            all(s in t for s in ('id="sendModal"', 'id="sendPreview"',
                                 'id="sendWhatsApp"', 'function sendCopy',
                                 'navigator.share', 'function sendEmail')),
        'EYE: each picker card gets an eye that opens the quick view':
            "eye.className = 'pick-eye'" in t and 'pickPeek(card, r.view)'
            in t and 'ev.stopPropagation()' in t,
        '  over the picker, with Back to list and Add to the day':
            'function pickPeek' in t and "'Back to list'" in t
            and "'Add to '" in t and '#quickLookModal.is-over' in t,
        'DRAG: week columns and month cells share one group':
            "group: 'meal-days'" in t and 'Object.assign({}, MEAL_DRAG'
            in t and "draggable: '.month-chip'" in t,
        '  a drop on another day posts Move, with dragged=1 and the order':
            'function dropMove' in t and "put('dragged', '1')" in t
            and '{% url "move_meal_entry" %}' in t,
        '  the month cell carries its date':
            'data-day="{{ cell.date|date:\'Y-m-d\' }}"' in t,
        '  the day under the pointer is outlined':
            '.month-cell.is-drop, .week-col-body.is-drop' in t,
        '  and the page offers Undo':
            'data-move-undo' in t and 'name="undo" value="1"' in t,
        'SERVER: move keeps the drop order and remembers the undo':
            "_drop_order(when, request.POST.get('order', ''))" in v
            and "request.session['meal_move_undo']" in v
            and "request.session.pop('meal_move_undo', None)" in v,
        '  and the picker rows carry their quick-view address':
            "'view': reverse('recipe_quicklook', args=[r.recipe_id])" in v,
    }


head('1. THE SOURCE')
T_NOW, V_NOW = read(TPL), read(VIEW)
for m, got in claims(T_NOW, V_NOW).items():
    ok(got, m)
ok(os.path.isfile(SEND), 'meal_send.py: the text and the email')
sd = read(SEND)
ok("__all__ = ['meal_plan_send']" in sd,
   '  only the view leaves it - recipes/__init__ star-imports it')
ok("path('meal_plans/send/', views.meal_plan_send" in read(J(PG, 'urls.py')),
   '  routed at meal_plans/send/')
ok('allowed_recipients' in sd and "'That address is not a household "
   "member.'" in sd, '  the email goes to the household roster only (B9)')
ok(not os.path.isfile(J(PG, 'templates', 'meal_plan_send_email.html')),
   '  the email is built in Python, not a page template the house-style '
   'suites would count')
ok('%-d' not in sd, '  and no %-d in a strftime')
ok(T_NOW.count('{%') == T_NOW.count('%}'),
   'the planner template tags balance')

head('2. THE CONTROL')
B = TPL + SUFFIX
if os.path.isfile(B) and os.path.isfile(VIEW + SUFFIX):
    held = [m for m, got in claims(read(B), read(VIEW + SUFFIX)).items()
            if got]
    ok(not held, 'CONTROL: not one claim held before RA16', held)
else:
    skip('the control', 'no .bak_ra16 beside the template')

head('3. DRIVEN (database; no network)')
import datetime as dt                                       # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
_dj.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']

have_db = False
try:
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import Permission, User
    from django.core import mail
    from django.urls import reverse
    from pages.models import MealEntry, Recipe
    connection.ensure_connection()
    MealEntry.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('sections 3 and 4 (database)', str(_e).split('\n')[0][:70])

MON = dt.date(2031, 11, 24)
DAYS = [MON + dt.timedelta(days=i) for i in range(7)]
ISO = [d.strftime('%Y-%m-%d') for d in DAYS]
PAGES = {}

if have_db:
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            ed = User.objects.create_user('ra16e', 'ra16e@example.com', 'pw')
            rd = User.objects.create_user('ra16r', 'ra16r@example.com', 'pw')
            for cn in ('can_access_recipes', 'can_edit_recipes'):
                ed.user_permissions.add(Permission.objects.get(codename=cn))
            rd.user_permissions.add(
                Permission.objects.get(codename='can_access_recipes'))
            E_, R_ = Client(), Client()
            E_.force_login(ed)
            R_.force_login(rd)

            def rec(n):
                return Recipe.objects.create(recipe_name=n, servings=6,
                                             prep_time=10, cook_time=20)
            names = ['Chicken Kritharaki', 'Lamb Chops', 'Kebabs', 'Squash',
                     'Salad', 'Ribs', '<b>Fish & chips</b>']
            R = dict((n, rec(n)) for n in names)

            def mk(day, name, order, of=None):
                return MealEntry.objects.create(
                    date=day, recipe=R[name], servings=4, sort_order=order,
                    created_by=ed, leftover_of=of)
            krit = mk(DAYS[0], 'Chicken Kritharaki', 0)
            mk(DAYS[1], 'Lamb Chops', 0)
            keb = mk(DAYS[2], 'Kebabs', 0)
            squ = mk(DAYS[2], 'Squash', 1)
            sal = mk(DAYS[2], 'Salad', 2)
            ribs = mk(DAYS[3], 'Ribs', 0)

            URL = '/meal_plans/send/'

            def words(view, day, c=E_):
                r = c.get(URL, {'view': view, 'date': day})
                return r.status_code, (json.loads(r.content.decode())
                                       if r.status_code == 200 else {})

            st, w = words('week', ISO[0])
            want = ['Mon (24th Nov): Chicken Kritharaki',
                    'Tue (25th Nov): Lamb Chops',
                    'Wed (26th Nov): Kebabs',
                    '                Squash',
                    '                Salad',
                    'Thu (27th Nov): Ribs']
            lines = w.get('text', '').split('\n')
            ok(st == 200 and lines[2:] == want,
               'THE WEEK AS DEMETRI WROTE IT: one line a day, a day\'s '
               'other meals lined up under its first, empty days left out',
               '\n'.join(lines))
            ok(w.get('subject') == 'Meal plan - 24 Nov to 30 Nov 2031',
               '  headed with the week', w.get('subject'))
            # RA17, 23 Nov 2026 - NO ``` BLOCK ANY MORE. Demetri's month
            # arrived in WhatsApp with only its first line; the block was
            # the only unusual thing in it. The same plain lines as Copy.
            ok(w.get('whatsapp', '').endswith('\n'.join(want)) and
               '```' not in w.get('whatsapp', ''),
               '  WhatsApp gets the same lines, with no code block (RA17)')
            st, m = words('month', ISO[3])
            ok(m.get('subject') == 'Meal plan - November 2031' and
               '\n'.join(want) in m.get('text', ''),
               'THE MONTH: the same list for the 1st to the 30th')
            st, d1 = words('day', ISO[2])
            ok(d1.get('text', '').split('\n')[2:] ==
               ['Wed (26th Nov): Kebabs', '                Squash',
                '                Salad'], 'THE DAY: that day only')
            st, d0 = words('day', ISO[5])
            ok(d0.get('empty') and 'Nothing planned yet.' in d0['text'],
               'AN EMPTY DAY says so rather than sending nothing')
            ok([p['email'] for p in w.get('people', [])][:1] ==
               ['ra16e@example.com'],
               'WHO IT CAN GO TO: you first, then the household roster')
            st, rw = words('week', ISO[0], R_)
            ok(st == 200 and 'people' not in rw,
               '  a reader can read and copy it, and is offered no email')

            def post(c, body):
                return c.post(URL, json.dumps(body),
                              content_type='application/json')
            mail.outbox = []
            r = post(E_, {'view': 'month', 'date': ISO[0],
                          'to': ['ra16e@example.com']})
            ok(r.status_code == 200 and len(mail.outbox) == 1,
               'EMAILED: one message', r.content[:200])
            if mail.outbox:
                msg = mail.outbox[0]
                html = msg.alternatives[0][0] if msg.alternatives else ''
                ok(msg.to == ['ra16e@example.com'] and
                   msg.subject == 'Meal plan - November 2031',
                   '  to the address chosen, headed with the month')
                ok(html.count('<th ') == 7 and 'Kebabs' in html and
                   html.count('<tr>') >= 6,
                   '  THE MONTH IS A CALENDAR: seven columns, whole weeks')
            mail.outbox = []
            mk(DAYS[4], '<b>Fish & chips</b>', 0)
            post(E_, {'view': 'week', 'date': ISO[0],
                      'to': ['ra16e@example.com']})
            html = (mail.outbox[0].alternatives[0][0]
                    if mail.outbox else '')
            ok('&lt;b&gt;Fish &amp; chips&lt;/b&gt;' in html and
               '<b>Fish' not in html,
               '  A NAME IS A PERSON\'S WORDS: escaped in the email')
            mail.outbox = []
            post(E_, {'view': 'day', 'date': ISO[2],
                      'to': ['ra16e@example.com']})
            html = (mail.outbox[0].alternatives[0][0]
                    if mail.outbox else '')
            ok('Squash' in html and '30 min' in html and
               '4 servings' in html,
               '  THE DAY LOOKS LIKE THE DAY VIEW: each meal with its time '
               'and servings')
            mail.outbox = []
            r = post(E_, {'view': 'week', 'date': ISO[0],
                          'to': ['stranger@example.org']})
            ok(r.status_code == 403 and not mail.outbox,
               'REFUSED: an address outside the household (B9)')
            r = post(R_, {'view': 'week', 'date': ISO[0],
                          'to': ['ra16r@example.com']})
            ok(r.status_code == 403 and not mail.outbox,
               'REFUSED: a reader cannot email from Alivente')
            r = post(E_, {'view': 'week', 'date': ISO[0], 'to': []})
            ok(r.status_code == 400, '  nor can nobody be chosen')

            # ---- THE DROP
            MOVE = '/meal_plans/move/'
            r = E_.post(MOVE, {
                'meal_entry_id': ribs.meal_entry_id, 'date': ISO[2],
                'view': 'week', 'from_date': ISO[0], 'dragged': '1',
                'order': '%d,%d,%d,%d' % (keb.meal_entry_id,
                                          ribs.meal_entry_id,
                                          squ.meal_entry_id,
                                          sal.meal_entry_id)})
            wed = list(MealEntry.objects.filter(date=DAYS[2])
                       .order_by('sort_order').values_list(
                           'recipe__recipe_name', flat=True))
            ok(r.status_code == 302 and
               wed == ['Kebabs', 'Ribs', 'Squash', 'Salad'],
               'A DROP ON WEDNESDAY moves Ribs there, WHERE IT WAS LET GO',
               (r.status_code, wed))
            ok('view=week' in r['Location'] and ISO[0] in r['Location'],
               '  and lands back on the week you were looking at',
               r['Location'])
            p = E_.get(r['Location']).content.decode()
            ok('data-move-undo' in p and 'Moved &ldquo;Ribs&rdquo; to Wed'
               in p, 'THE PAGE OFFERS UNDO, once')
            p = E_.get(r['Location']).content.decode()
            ok('data-move-undo' not in p, '  and not again on a refresh')
            r = E_.post(MOVE, {'meal_entry_id': ribs.meal_entry_id,
                               'date': ISO[3], 'view': 'week',
                               'from_date': ISO[0], 'undo': '1'})
            ribs.refresh_from_db()
            ok(ribs.date == DAYS[3], 'UNDO puts Ribs back on Thursday')
            left = mk(DAYS[1], 'Chicken Kritharaki', 1, of=krit)
            E_.post(MOVE, {'meal_entry_id': krit.meal_entry_id,
                           'date': ISO[4], 'view': 'month',
                           'from_date': ISO[0], 'dragged': '1',
                           'order': str(krit.meal_entry_id)})
            krit.refresh_from_db()
            left.refresh_from_db()
            ok(krit.date == DAYS[4] and left.date == DAYS[5],
               'A DROP IS A MOVE: the leftovers travel with their meal, '
               'keeping the gap', (krit.date, left.date))
            p = E_.get('/meal_plans/planner/?view=month&date=%s' % ISO[0]) \
                .content.decode()
            ok('with its leftovers' in p, '  and Undo says so')
            krit_back = E_.post(MOVE, {
                'meal_entry_id': krit.meal_entry_id, 'date': ISO[0],
                'view': 'month', 'from_date': ISO[0], 'undo': '1'})
            krit.refresh_from_db()
            left.refresh_from_db()
            ok(krit.date == DAYS[0] and left.date == DAYS[1],
               '  and undoing it brings both back', krit_back.status_code)
            r = R_.post(MOVE, {'meal_entry_id': ribs.meal_entry_id,
                               'date': ISO[2], 'dragged': '1'})
            ribs.refresh_from_db()
            ok(r.status_code == 403 and ribs.date == DAYS[3],
               'A READER cannot move a meal by dropping it either')

            # ---- THE PICKER ROWS
            r = E_.get('/meal_plans/picker_recipes/', {'search': 'Squash'})
            rows = json.loads(r.content.decode()).get('rows', [])
            ok(rows and rows[0].get('view') ==
               reverse('recipe_quicklook', args=[R['Squash'].recipe_id]),
               'THE PICKER\'S ROWS carry the quick-view address', rows[:1])

            # ---- THE PAGES, for section 4
            for v in ('month', 'week', 'day'):
                PAGES[v] = E_.get('/meal_plans/planner/?view=%s&date=%s'
                                  % (v, ISO[0])).content.decode()
            ok(all('id="sendModal"' in PAGES[v] for v in PAGES),
               'EVERY VIEW has Send')
            rp = R_.get('/meal_plans/planner/?view=week&date=%s' % ISO[0]) \
                .content.decode()
            ok('id="sendModal"' in rp, '  a reader gets Send too')
            ok('id="sendPeople"' not in rp and 'id="sendEmailBtn"' not in rp,
               '  but no email in it')
            ok('new Sortable' not in rp and 'MEAL_DRAG' not in rp,
               '  and no drag at all')
            ok(PAGES['month'].count('class="month-cell') ==
               PAGES['month'].count('data-day="2031-') +
               PAGES['month'].count('month-cell is-out'),
               'EVERY MONTH DAY carries its date - a drop target')

            # ---- WHAT THE BROWSER WILL ASK FOR, ASKED NOW. Playwright's
            # sync API runs an event loop on this thread, and Django
            # refuses database work from inside one - so the answers are
            # fetched here and the route below only hands them over.
            PRE = {}

            def pre(key, path, **q):
                resp = E_.get(path, q)
                PRE[key] = (resp.status_code, resp.content,
                            resp.get('Content-Type', 'text/html'))
            pre('/meal_plans/send/', '/meal_plans/send/', view='week',
                date=ISO[0])
            pre('/meal_plans/day_entries/', '/meal_plans/day_entries/',
                date=ISO[1])
            pre('/meal_plans/picker_recipes/', '/meal_plans/picker_recipes/',
                search='Squash')
            QL = reverse('recipe_quicklook', args=[R['Squash'].recipe_id])
            pre(QL, QL)

            # ---- 4. RENDERED
            head('4. RENDERED - A REAL DROP, THE EYE AND SEND')
            try:
                from playwright.sync_api import sync_playwright
            except Exception:
                sync_playwright = None
            LOCAL = J(ROOT, 'static', 'vendor', 'sortablejs',
                      'Sortable.min.js')
            FIX = J(ROOT, 'test_fixture_bootstrap413.css')
            VEND = None
            for cand in ('/tmp/claude-0/ra16vend/node_modules',
                         J(ROOT, 'node_modules')):
                if os.path.isfile(J(cand, 'jquery', 'dist',
                                    'jquery.min.js')):
                    VEND = cand
                    break
            if sync_playwright is None or not os.path.isfile(LOCAL):
                skip('section 4', 'no Playwright or no local Sortable')
            else:
                caught = {}

                def route(r):
                    url = r.request.url
                    path = re.sub(r'^https?://[^/]+', '', url)
                    if '/meal_plans/move/' in url:
                        caught['move'] = r.request.post_data or ''
                        return r.fulfill(status=200, body=b'moved',
                                         content_type='text/plain')
                    if 'Sortable' in url:
                        with open(LOCAL, 'rb') as f:
                            return r.fulfill(
                                status=200, body=f.read(),
                                content_type='application/javascript')
                    # THE PAGE'S BOOTSTRAP, from the repo's own fixture -
                    # test_week_drag's answer. Without it the month grid is
                    # laid out by the browser's defaults, not the site's,
                    # and a drag there proves nothing about the live page.
                    if 'bootstrap' in url and url.endswith('.css') \
                            and os.path.isfile(FIX):
                        with open(FIX, 'rb') as f:
                            return r.fulfill(status=200, body=f.read(),
                                             content_type='text/css')
                    if VEND:
                        for k, pth in (
                                ('jquery', 'jquery/dist/jquery.min.js'),
                                ('popper', 'popper.js/dist/umd/'
                                 'popper.min.js'),
                                ('bootstrap.min.js', 'bootstrap/dist/js/'
                                 'bootstrap.min.js'),
                                ('bootstrap.min.css', 'bootstrap/dist/css/'
                                 'bootstrap.min.css')):
                            if k in url:
                                with open(J(VEND, pth), 'rb') as f:
                                    return r.fulfill(status=200,
                                                     body=f.read())
                    if path.startswith('/meal_plans/') or \
                            path.startswith('/recipe/'):
                        if r.request.method == 'POST':
                            caught.setdefault('posts', []).append(path)
                            return r.fulfill(status=200, body=b'{}')
                        got = PRE.get(path.split('?')[0])
                        if got:
                            return r.fulfill(status=got[0], body=got[1],
                                             content_type=got[2])
                        return r.fulfill(status=404, body=b'')
                    return r.fulfill(status=200, body=b'',
                                     content_type='text/plain')

                def page(br, html, w=1280):
                    pg = br.new_page(viewport={'width': w, 'height': 1100})
                    pg.route(re.compile(r'^https?://'), route)
                    pg.set_content(html.replace(
                        '<head>', '<head><base href="http://127.0.0.1/">'),
                        wait_until='load')
                    pg.wait_for_timeout(700)
                    return pg

                def drag(pg, src, dst, hold=None):
                    a = pg.query_selector(src).bounding_box()
                    b = pg.query_selector(dst).bounding_box()
                    pg.mouse.move(a['x'] + a['width'] / 2,
                                  a['y'] + a['height'] / 2)
                    pg.mouse.down()
                    for i in range(1, 16):
                        pg.mouse.move(
                            a['x'] + a['width'] / 2 +
                            (b['x'] + b['width'] / 2 - a['x'] -
                             a['width'] / 2) * i / 15.0,
                            a['y'] + a['height'] / 2 +
                            (b['y'] + b['height'] * 0.7 - a['y'] -
                             a['height'] / 2) * i / 15.0)
                        pg.wait_for_timeout(30)
                    if hold:
                        hold(pg)
                    pg.mouse.up()
                    pg.wait_for_timeout(900)

                with sync_playwright() as pw:
                    br = pw.chromium.launch()
                    pg = page(br, PAGES['month'])
                    src = ('.month-cell[data-day="%s"] .month-chip'
                           % ISO[0])
                    dst = '.month-cell[data-day="%s"]' % ISO[5]
                    seen = {}

                    def during(p):
                        seen['drop'] = p.evaluate(
                            "() => [...document.querySelectorAll('.is-drop')]"
                            ".map(e => e.getAttribute('data-day'))")
                    drag(pg, src, dst, during)
                    ok(seen.get('drop') == [ISO[5]],
                       'MONTH: while dragging, the day under the pointer '
                       'is outlined', seen)
                    body = caught.get('move', '')
                    ok('dragged=1' in body and 'date=%s' % ISO[5] in body
                       and 'meal_entry_id=%d' % krit.meal_entry_id in body,
                       '  and letting go POSTS Move for that meal and day',
                       body[:300])
                    pg.close()

                    caught.clear()
                    pg = page(br, PAGES['week'])
                    src = ('.week-col-body[data-day="%s"] .week-chip'
                           % ISO[1])
                    dst = '.week-col-body[data-day="%s"]' % ISO[6]
                    drag(pg, src, dst)
                    body = caught.get('move', '')
                    ok('dragged=1' in body and 'date=%s' % ISO[6] in body,
                       'WEEK: a meal dropped on an EMPTY Sunday moves there',
                       body[:300])
                    pg.close()

                    caught.clear()
                    pg = page(br, PAGES['week'])
                    pg.evaluate('sendLoad()')
                    pg.wait_for_timeout(800)
                    href = pg.get_attribute('#sendWhatsApp', 'href') or ''
                    pre = pg.text_content('#sendPreview') or ''
                    # RA17 - the preview is a day-by-meal list now.
                    ok(href.startswith('https://wa.me/?text=') and
                       'Wed (26th Nov)' in pre and 'Kebabs' in pre,
                       'SEND: the dialog shows the plan and WhatsApp '
                       'carries it', (href[:60], pre[:80]))
                    ok(pg.evaluate("document.querySelectorAll("
                                   "'#sendPeople input').length") >= 1,
                       '  with the household to tick for email')
                    pg.close()

                    if not VEND:
                        skip('the eye in a browser', 'no local jQuery and '
                             'Bootstrap 4.1.3 to drive the dialogs')
                    else:
                        caught.clear()
                        pg = page(br, PAGES['week'])
                        pg.evaluate("openPicker('%s', 'Tue 25')" % ISO[1])
                        pg.wait_for_timeout(1200)
                        n = pg.evaluate("document.querySelectorAll("
                                        "'#pickerList .pick-eye').length")
                        ok(n >= 1, 'EYE: every recipe card in the picker '
                           'has one (%d)' % n)
                        pg.click('#pickerList .recipe-option .pick-eye')
                        pg.wait_for_timeout(1200)
                        st = pg.evaluate("""() => {
                            const q = document.getElementById('quickLookModal');
                            const p = document.getElementById('pickerModal');
                            const f = q.querySelector('.ql-pickfoot');
                            return [q.classList.contains('show'),
                                    q.classList.contains('is-over'),
                                    p.classList.contains('show'),
                                    f ? f.textContent.trim() : ''];
                        }""")
                        ok(st[0] and st[1] and st[2],
                           '  pressing it opens the quick view OVER the '
                           'picker', st)
                        ok('Back to list' in st[3] and 'Add to Tue 25'
                           in st[3], '  with Back to list and Add to the '
                           'day', st[3])
                        ok(not caught.get('posts'),
                           '  and adds nothing', caught.get('posts'))
                        pg.click('.ql-pickfoot .action-secondary')
                        pg.wait_for_timeout(900)
                        st = pg.evaluate("""() => [
                            document.getElementById('quickLookModal')
                                .classList.contains('show'),
                            document.getElementById('pickerModal')
                                .classList.contains('show'),
                            document.body.classList.contains('modal-open')]
                        """)
                        ok(st == [False, True, True],
                           '  BACK TO LIST closes it and the picker is still '
                           'open and scrolls', st)
                        pg.close()
                    br.close()
            raise Rollback
    except Rollback:
        pass

head('5. HELP AND REGISTERED')
g = read(GUIDE)
ok('drag a meal onto any other day' in g and
   'Not yet, and coming' not in g.split('data-tab-slug="mp-build"')[1]
   .split('</article>')[0], 'HELP: dragging to another day, no longer '
   '"coming"')
ok('Have a look before you add.' in g, 'HELP: the eye in the picker')
ok('data-tab-slug="mp-send"' in g and 'Send&hellip;' in g,
   'HELP: Sending a plan')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
