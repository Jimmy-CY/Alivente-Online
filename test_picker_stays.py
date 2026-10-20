# -*- coding: utf-8 -*-
"""test_picker_stays.py - round PS-1, 19 Oct 2026.

RELEASE 4, PUSH 2. THE PICKER ADDS ON CLICK, AND STAYS OPEN.

Demetri: "if I want to add a few recipes/sides to a day, currently, I
would have to click on '+ Add Recipe', then filter, then click on the
recipe, then click on '+ Add Meal', then click on '+ Add Recipe'
again ...... and repeat."

THE CLAIM THAT MATTERS: four recipes onto a Saturday takes ONE open
and the filters are still set at the end. Section 4 does exactly
that, in a browser, and reads the filter box afterwards.

    before   open-filter-click-Add, four times      ~20 actions
    after    open-filter-click-click-click-click    7 actions

The re-filtering is the real cost. C19 makes the dialog forget its
filters on every open - right for a dialog you use once, a tax on one
you use four times - AND C19 IS UNCHANGED BY THIS ROUND. Section 1
asks whether openPicker still clears them. They survive while the
dialog is open; they still reset when it opens.

HOW THE BROWSER HALF IS DRIVEN, and why it is not a live server.
PF-2's renderer established this on the 19th: call the real endpoints
through the test client, capture the REAL bytes, then replace
window.fetch with a function that returns exactly those and RECORDS
what was asked. Real server output, real client rendering, only the
HTTP hop stubbed.

A live server was tried first and cost more than it proved: a page
served by set_content sits on about:blank, where every relative url
the dialog fetches is invalid, so the list came back empty with no
error at all.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One description of a day, asked three times; the
      form post still redirects; no Servings field; no Add Meal; the
      strip and its remove; C19 still clearing on open.

  2   THE CONTROL. Re-asked of the pre-round files.

  3   THE SERVER, driven directly. Four adds, a second helping, a
      remove, a form post that still redirects, and a date nobody can
      read refused.

  4   THE BROWSER, with fetch stubbed and recorded. Four clicks, one
      open, the filter still set, the strip drawn, and NO SERVINGS in
      any of the four posts.

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
import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_pickerstays'
ME = 'test_picker_stays.py'
PATCHER = 'apply_picker_stays.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PS-1, 19 Oct 2026'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
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


def claims(bundle):
    v = T.python_code_only(bundle[VIEW], payloads=True)
    u = T.python_code_only(bundle[URLS], payloads=True)
    t = T.code_only(bundle[TPL])
    c = {}

    c['one description of what is on a day'] = (
        'def day_payload(' in v)
    # THE CALLS, NOT THE DECLARATION - the trap PB-2 fell into an hour
    # earlier in this same push, with planner_back.
    c['asked three times - the dialog opening, an add and a '
      'remove'] = (
        len(re.findall(r'(?<!def )day_payload\(when\)', v)) == 3)
    c['and there is a read-tier endpoint for the first of those'] = (
        'def meal_day_entries(' in v and
        "name='meal_day_entries'" in u)

    # THE FORM POST IS UNCHANGED. The Move dialog, the note form and
    # the menus all still post normally and expect to be sent back.
    for name in ('add_meal_entry', 'remove_meal_entry'):
        chunk = v.split('def %s' % name, 1)
        chunk = re.split(r'\n@|\ndef ', chunk[1])[0] if len(chunk) > 1 \
            else ''
        c['%s still redirects for a form post' % name] = (
            'planner_back(' in chunk)
        c['and answers in JSON when asked (%s)' % name] = (
            "request.POST.get('json')" in chunk)

    # THE FIELD AND THE BUTTON ARE GONE.
    c['the Servings field is gone'] = (
        bool(t) and 'id="pickerServings"' not in t)
    c['and the Add Meal button with it'] = (
        bool(t) and 'id="pickerAdd"' not in t)
    c['Done is what closes it'] = ('id="pickerDone"' in t)

    # AND THE STRIP IS THERE. Without it a mis-click is a row nobody
    # can see - the round should not exist without this.
    c['the dialog shows what is on the day'] = (
        'id="pickerDayList"' in t)
    c['each row removable in place'] = ('function pickDrop(' in t)
    c['clicking a card is the add'] = ('function pickAdd(' in t)

    # C19 IS UNCHANGED. The filters survive WHILE the dialog is open -
    # that is this round - and still reset when it opens.
    _open = t.split('function openPicker(', 1)
    c['and C19 still holds: the filters reset ON OPEN'] = (
        len(_open) > 1 and 'pfClear(true)' in _open[1][:2000])
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
WAS = claims(BEFORE)
held = [m for m, got in WAS.items() if got]
# THREE OF THESE CLAIMS ARE PRESERVATION CLAIMS, and they are
# SUPPOSED to hold before and after: C19's reset on open, and the two
# redirects that every other form on this page still depends on. A
# round can assert that it did not break something, and the control's
# job is to separate those from the claims it established.
#
# This is not the vacuous-absence trap RD-1, RD-2 and MB-2 all hit -
# those were claims about something NOT being somewhere, true of a
# file where the subject did not exist. These are about things that
# ARE there and must stay.
KEEPS = sorted([
    'add_meal_entry still redirects for a form post',
    'remove_meal_entry still redirects for a form post',
    'and C19 still holds: the filters reset ON OPEN',
])
ok(sorted(held) == KEEPS,
   'the only claims that held before are the three this round KEEPS '
   'rather than establishes',
   'what held: %r\nexpected: %r' % (sorted(held), KEEPS))
OLD_T = T.code_only(BEFORE[TPL])
ok('id="pickerServings"' in OLD_T,
   'CONTROL: there really was a Servings field')
ok('id="pickerAdd"' in OLD_T,
   'CONTROL: and an Add Meal button you had to press')
ok('function pickRecipe(' in OLD_T,
   'CONTROL: and clicking a card only SELECTED it')


# ==========================================================================
head('3. THE SERVER, DRIVEN DIRECTLY')
# ==========================================================================
JQ = "\nwindow.jQuery = window.$ = function (sel) {\n  if (typeof sel === 'function') { setTimeout(sel, 0); return; }\n  var els = (sel && sel.nodeType) ? [sel]\n          : Array.prototype.slice.call(document.querySelectorAll(sel || ''));\n  var api = {\n    modal: function (w) { els.forEach(function (e) {\n        if (w === 'show') { e.classList.add('show'); e.style.display='block'; }\n        else if (w === 'hide') { e.classList.remove('show'); e.style.display='none';\n          e.dispatchEvent(new Event('hidden.bs.modal')); } }); return api; },\n    hasClass: function (c) { return els.some(function (e) { return e.classList.contains(c); }); },\n    on: function (ev, fn) { ev.split(' ').forEach(function (o) {\n        els.forEach(function (e) { e.addEventListener(o, fn); }); }); return api; },\n    off: function () { return api; }, find: function () { return api; },\n    each: function () { return api; },\n    val: function () { return els[0] ? els[0].value : ''; },\n    text: function () { return els[0] ? els[0].textContent : ''; }\n  };\n  return api;\n};\n"

STUB = "(d) => {\n  window.__posts = [];\n  window.__addN = 0;\n  window.fetch = function (url, opts) {\n    opts = opts || {};\n    var body = opts.body ? String(opts.body) : '';\n    if ((opts.method || 'GET').toUpperCase() === 'POST') {\n      window.__posts.push({url: String(url), body: body});\n      var text = body.indexOf('meal_entry_id') >= 0\n        ? d.rem : d.adds[Math.min(window.__addN++, d.adds.length - 1)];\n      return Promise.resolve({ok: true, status: 200,\n        json: function () { return Promise.resolve(JSON.parse(text)); },\n        text: function () { return Promise.resolve(text); }});\n    }\n    var g = String(url).indexOf('day_entries') >= 0 ? d.day0 : d.rows;\n    return Promise.resolve({ok: true, status: 200,\n      json: function () { return Promise.resolve(JSON.parse(g)); },\n      text: function () { return Promise.resolve(g); }});\n  };\n}"


django_up = False
cl = None
recs = []
SAT = '2026-10-24'
SATD = dt.date(2026, 10, 24)
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
    dj.DEBUG = True
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if django_up:
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from django.urls import reverse
    from pages.models import MealEntry, Recipe, RecipeCourse

    u = User.objects.create_user(username='ps1', password='x',
                                 email='ps1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    course = RecipeCourse.objects.create(name='Main', display_order=1)
    for n in ('Fakes Soupa', 'Moussaka', 'Greek Salad', 'Tzatziki',
              'Baklava', 'Briam'):
        r = Recipe.objects.create(recipe_name=n, servings=5,
                                  prep_time=10, cook_time=20)
        r.courses.add(course)
        recs.append(r)
    cl = Client()
    cl.force_login(u)

    payload = None
    codes = []
    for i in range(4):
        resp = cl.post(reverse('add_meal_entry'),
                       {'recipe_id': recs[i].recipe_id, 'date': SAT,
                        'json': '1', 'view': 'week'})
        codes.append(resp.status_code)
        if resp.status_code == 200:
            payload = json.loads(resp.content.decode('utf-8'))

    ok(codes == [200] * 4,
       'four adds, each answered with the day', 'codes %r' % (codes,))
    ok(payload and len(payload['entries']) == 4,
       'and the fourth answer holds all four',
       'held %r' % (payload or {}).get('entries'))

    # THE SERVINGS ARE THE RECIPE'S OWN YIELD. Demetri: "it must just
    # add the standard servings for that recipe." Nothing was sent.
    servings = [e['servings'] for e in (payload or {}).get('entries', [])]
    ok(servings == [5, 5, 5, 5],
       'and each is the RECIPE\'s own yield, with no servings sent at '
       'all', 'recorded %r, the recipes make 5' % (servings,))

    # A SECOND CLICK IS A SECOND HELPING, not an error.
    resp = cl.post(reverse('add_meal_entry'),
                   {'recipe_id': recs[0].recipe_id, 'date': SAT,
                    'json': '1', 'view': 'week'})
    p2 = json.loads(resp.content.decode('utf-8'))
    same = [e for e in p2['entries']
            if e['recipe_id'] == recs[0].recipe_id]
    ok(len(same) == 2,
       'a second click on the same recipe is a second helping',
       'found %d' % len(same))

    # REMOVE ANSWERS WITH THE DAY TOO.
    resp = cl.post(reverse('remove_meal_entry'),
                   {'meal_entry_id': p2['entries'][0]['id'],
                    'json': '1', 'view': 'week'})
    p3 = json.loads(resp.content.decode('utf-8'))
    ok(len(p3['entries']) == 4,
       'and remove answers with the day as well, so the strip and the '
       'calendar cannot disagree')

    # THE FORM POST IS UNCHANGED - the Move dialog and the note form
    # still post normally and expect to be sent back.
    resp = cl.post(reverse('add_meal_entry'),
                   {'recipe_id': recs[0].recipe_id, 'date': SAT,
                    'view': 'day'})
    ok(resp.status_code == 302 and
       'view=day' in (resp.get('Location') or ''),
       'CONTROL: without json it still redirects, carrying the view',
       'got %s %r' % (resp.status_code, resp.get('Location')))

    # THE DAY ENDPOINT, and a date nobody can read.
    resp = cl.get(reverse('meal_day_entries'), {'date': SAT})
    ok(resp.status_code == 200,
       'the day endpoint answers', 'got %s' % resp.status_code)
    ok(cl.get(reverse('meal_day_entries'),
              {'date': 'the day after tomorrow'}).status_code == 400,
       'and refuses a date it cannot read rather than guessing one')

    # READ-TIER, like the planner it serves.
    stranger = User.objects.create_user(username='no', password='x',
                                        email='n@example.test')
    c2 = Client()
    c2.force_login(stranger)
    ok(c2.get(reverse('meal_day_entries'),
              {'date': SAT}).status_code in (302, 403),
       'and somebody without can_access_recipes is refused')


# ==========================================================================
head('4. THE BROWSER - four clicks, one open')
# ==========================================================================
if not django_up or cl is None:
    skip('the browser checks', 'no database')
else:
    MealEntry.objects.filter(date=SATD).delete()
    html = cl.get('/meal_plans/',
                  {'view': 'month',
                   'date': '2026-10-19'}).content.decode('utf-8')
    rows_json = cl.get(reverse('picker_recipes')).content.decode('utf-8')
    day0 = cl.get(reverse('meal_day_entries'),
                  {'date': SAT}).content.decode('utf-8')
    adds = []
    for i in range(4):
        adds.append(cl.post(
            reverse('add_meal_entry'),
            {'recipe_id': recs[i].recipe_id, 'date': SAT, 'json': '1',
             'view': 'week'}).content.decode('utf-8'))
    ids = [e['id'] for e in json.loads(adds[-1])['entries']]
    rem = cl.post(reverse('remove_meal_entry'),
                  {'meal_entry_id': ids[0], 'json': '1',
                   'view': 'week'}).content.decode('utf-8')

    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1200, 'height': 950})
            # jQuery is loaded from a CDN this sandbox cannot reach, so
            # enough of it is stood up to let the REAL page code run -
            # and it goes in the document, ahead of every script the
            # page carries, because the page's own $(function(){}) runs
            # at load and would throw first.
            pg.set_content(
                html.replace('<head>', '<head><script>' + JQ +
                             '</script>', 1), wait_until='load')
            pg.evaluate(STUB, {'rows': rows_json, 'day0': day0,
                               'adds': adds, 'rem': rem})
            pg.evaluate("(d) => openPicker(d, 'Saturday 24 October')",
                        SAT)
            pg.wait_for_timeout(400)

            ok(pg.evaluate("() => $('#pickerModal').hasClass('show')"),
               'the dialog opens')
            n_cards = pg.evaluate(
                "() => document.querySelectorAll('.recipe-option').length")
            ok(n_cards == 6, 'with the library in it',
               'drew %d cards' % n_cards)
            ok(not pg.evaluate(
                "() => !!document.getElementById('pickerAdd')"),
               'and no Add Meal button')
            ok(not pg.evaluate(
                "() => !!document.getElementById('pickerServings')"),
               'and no Servings field')

            # A FILTER, SET ONCE, AND FOUR CLICKS.
            pg.evaluate(
                "() => { document.getElementById('pickerSearch')"
                ".value = 'a'; }")
            for i in range(4):
                pg.evaluate(
                    "(i) => { var c = document.querySelectorAll("
                    "'.recipe-option'); if (c[i]) { c[i].click(); } }", i)
                pg.wait_for_timeout(260)

            ok(pg.evaluate("() => $('#pickerModal').hasClass('show')"),
               'FOUR RECIPES ADDED AND THE DIALOG IS STILL OPEN')
            ok(pg.evaluate(
                "() => document.getElementById('pickerSearch').value")
               == 'a',
               'and the filter is still set - which is the twenty '
               'actions becoming seven')
            strip = pg.evaluate(
                "() => document.querySelectorAll('.picker-day-row')"
                ".length")
            ok(strip == 4, 'the strip shows all four',
               'showed %d' % strip)
            badges = pg.evaluate(
                "() => document.querySelectorAll('.pf-added').length")
            ok(badges == 4, 'and each card is marked as added',
               'marked %d' % badges)

            posts = pg.evaluate("() => window.__posts")
            ok(len(posts) == 4, 'four posts, one per click',
               'issued %d' % len(posts))
            ok(all('servings' not in p['body'] for p in posts),
               'and NOT ONE of them sent a servings value - the server '
               'takes the recipe\'s own yield')
            ok(all('json=1' in p['body'] for p in posts),
               'each asked for the day back rather than a redirect')

            # THE STRIP REMOVES IN PLACE - the undo a mis-click needs.
            pg.evaluate(
                "() => { var d = document.querySelector("
                "'.picker-day-drop'); if (d) { d.click(); } }")
            pg.wait_for_timeout(300)
            after = pg.evaluate(
                "() => document.querySelectorAll('.picker-day-row')"
                ".length")
            ok(after == 3,
               'and a row can be taken off from inside the dialog',
               'left %d' % after)
            pg.close()
            br.close()


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
# AFTER WHAT IT BUILDS ON, not "newest".
#
# This asserted ROUNDS[-1] == SUFFIX, which is true of a round
# delivered on its own and FALSE for seven of the eight in this push -
# only one of them can be last. Eight suites carried the same wrong
# claim, because each was written as though it would ship alone.
#
# The claim was reaching for something real: revert runs NEWEST FIRST,
# so a round must sit AFTER anything whose work it edits, or reverting
# the two in order restores the older round's text over the newer
# one. That is the 18 Oct bug and it cost a hand repair.
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_viewback']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose work it edits - so revert takes '
       'them off in the right order' % _dep)
# RETIRED - DB-1, 20 Oct 2026. This asked whether the round sat in
# the last eight entries of the register, which was true while push 2
# was the newest thing in it and false as soon as anything shipped
# after it. It is the same mistake as the `ROUNDS[-1] == SUFFIX` it
# replaced: a claim about a POSITION in a growing list expires
# whatever number is in it, so re-pinning would only move the date.
# The dependency claim above is the real one and does not expire.
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once',
   alv_rounds.ROUNDS.count(SUFFIX))
for frag in ('def day_payload(', 'function pickAdd('):
    ok(frag in gate, 'the gate pins %r' % frag)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_picker_stays as PATCH                          # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
