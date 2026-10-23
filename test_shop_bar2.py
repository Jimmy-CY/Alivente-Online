# -*- coding: utf-8 -*-
"""test_shop_bar2.py - round SB-2, 22 Oct 2026.

THE SHOPPING LIST BAR HAD TWO PRIMARIES ON STEP 2, AND ONE ON A STATE
WHERE NOTHING COULD HAPPEN.

Rendered in Chromium on 22 October, both widths, four states, and the
pictures went to Demetri before a line was changed - because both
questions in them are his:

    state 1  Generate List [primary]  Help  Back          one primary
    state 2  Done [primary]  Print [primary]  Help  Back  TWO
    state 3  identical to state 1 - Print is hidden again
    state 4  Generate List [primary]  Help  Back
             ... with no step 1 on the page to generate FROM

He decided: Done keeps the primary, Print becomes a secondary; and
Generate List is not offered when there is nothing it could generate.

NOBODY WROTE TWO PRIMARIES ON PURPOSE. SL-1 gave Print one on 3 October
when it was the only new control on the page; SL-2 gave Done one the
next day when it built the single bar. Neither round could see the
other state, and no suite in this tree counts primaries WITHIN one bar.
Section 1 counts them, per state, which is the instrument that was
missing.

AND STATE 4 IS THE FAULT DEMETRI REPORTED IN OCTOBER, THREE WEEKS ON.

    Print butoon brings up an empty list. Should not appear until
    shopping list has been defined.                      - 3 October

That was Print, and SL-1 fixed it. This is Generate List, on the page
where no ingredient has a shopping unit: the template gates the whole
two-step flow on {% if ingredients %}, so step 1 is not rendered at all
- and the bar above it still offered to generate from it.

NOT RENDERED, NOT hidden, AND NOT disabled. SL-1 chose hidden over
disabled because a disabled control still says you may press it and
then refuses, and said in the same comment that what it wanted was that
"the server never renders a usable Print for a list that cannot exist".
Here that is available, because the condition is known before the page
is sent.

A CONDITIONAL ATTRIBUTE WOULD HAVE BEEN WRONG, and section 1 refuses
one by name. The first draft wrote the condition INSIDE the tag. Most
instruments in this tree read a template as text, and they would then
have seen the word hidden in the tag and concluded the button always
ships hidden - test_meal_help renders the bar from raw template source
and counted one control fewer. It said so, which is why this is a
claim.

AND SL-2's OWN SUITE NEEDED NOTHING. It pins genBtn as always shipping
visible, and reads its page through as_left_by() - so from the moment
this round writes its backup, that suite reads the pre-SB-2 text, where
genBtn really did always ship visible. The first draft of this round
edited that claim and it FAILED, because as_left_by had already handed
the suite the backup. PG-1 built that on 18 October for exactly this,
and it worked on the first round that needed it.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One primary per state; Print is a secondary and
      keeps every guard SL-1 gave it; Generate List is wrapped, not
      attributed; setBar cannot reveal what the server withheld.

  2   THE CONTROL. Re-asked of .bak_shopbar2, where step 2 had two.

  3   DRIVEN AND RENDERED. All four states in Chromium at 1280 and
      390, the primaries counted off computed colour rather than off
      a class name, and the page with nothing to shop for driven for
      real.

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

SUFFIX = '.bak_shopbar2'
ME = 'test_shop_bar2.py'
PATCHER = 'apply_shop_bar2.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'SB-2, 22 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates',
                   'meal_plan_shopping_list.html')
GATE = os.path.join(ROOT, PS1)
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


# THE BAR IS A SLICE, and it is taken from code_only so a comment
# ABOUT a class cannot answer a question about a class. .find(), not
# .index(): against the reverted tree everything here still exists, but
# a later round that renames the wrapper would crash this rather than
# fail it.
def bar_of(src):
    code = T.code_only(src)
    a = code.find('<div class="page-action-buttons">')
    b = code.find('\n    </div>', a)
    return code[a:b] if 0 <= a < b else ''


def tags(bar):
    """id -> the opening tag, for every control on the bar."""
    out = {}
    for m in re.finditer(r'<(?:button|a)\b[^>]*>', bar):
        i = re.search(r'id="([^"]+)"', m.group(0))
        if i:
            out[i.group(1)] = m.group(0)
    return out


def claims(d):
    bar = bar_of(d[TPL])
    t = tags(bar)
    js = T.code_only_js(d[TPL])
    return {
        'Print is a SECONDARY, so step 2 has one primary':
            'action-secondary' in t.get('printBtn', ''),
        'Generate List is WRAPPED in a condition, not attributed':
            '{% if ingredients %}' in bar,
        'and setBar cannot reveal what the server withheld':
            'genBtn: step === 1 && ALV_CAN_GENERATE' in js,
        '  reading a flag rendered from the same condition':
            'var ALV_CAN_GENERATE = {% if ingredients %}' in d[TPL],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

BAR = bar_of(NOW[TPL])
TAG = tags(BAR)

# PRESERVATION, NOT CHANGE - and therefore OUTSIDE claims().
#
# Both of these were already true before SB-2, and the control said so
# on 22 October, correctly: its rule is that no claim of this round
# may have held before it, and a claim that did is a claim proving
# nothing about the round. They are still worth pinning - the point of
# the round is that step 2 ends with ONE primary, which is as much
# about Done keeping its primary as about Print losing one - so they
# are asked here, where the control does not re-ask them.
ok('action-primary' in TAG.get('doneBtn', ''),
   'PRESERVED: Done is still the primary, which is what Demetri chose')
ok('genBtn' in TAG and 'hidden' not in TAG['genBtn'],
   'PRESERVED: and nothing in the Generate tag itself says hidden - '
   'the first draft put the condition in an attribute, and text-reading '
   'instruments saw an unconditional hidden')
JS = T.code_only_js(NOW[TPL])

# ONE PRIMARY PER STATE, COUNTED. The instrument that was missing.
prim = sorted(k for k, v in TAG.items() if 'action-primary' in v)
ok(prim == ['doneBtn', 'genBtn'],
   'exactly two .action-primary controls on the bar - %s' % prim, prim)
ok('hidden' in TAG.get('doneBtn', '') and 'hidden' not in TAG.get(
    'genBtn', ''),
   '  and they are never on screen together: Generate List ships '
   'visible, Done ships hidden, and setBar swaps them')

# PRINT KEEPS EVERY GUARD SL-1 GAVE IT. A class change is not a
# licence to touch behaviour.
ok('hidden' in TAG.get('printBtn', ''),
   'GUARD: Print still ships hidden - SL-1 first guard, 3 October')
ok('disabled' not in TAG.get('printBtn', ''),
   '  still hidden rather than disabled')
ok('onclick="printList()"' in TAG.get('printBtn', ''),
   '  and still goes through printList()')
ok('hasPrintableList' in JS,
   '  and SL-1 second guard is still in the handler')
ok("_print.removeAttribute('hidden')" in JS,
   '  and generateShoppingList still reveals it with the list')

# AND GENERATE LIST IS NOT DISABLED EITHER.
ok('disabled' not in TAG.get('genBtn', ''),
   'Generate List is not disabled - a disabled control still says you '
   'may press it and then refuses')

# THE ORDER IS STILL A-BAR: primary, secondaries, back.
order = [m.group(1) for m in re.finditer(r'id="([^"]+)"', BAR)]
ok(order.index('doneBtn') < order.index('printBtn'),
   'A-BAR: Done comes before Print, which is primary before secondary',
   order)
ok(order.index('printBtn') < order.index('backLink'),
   '  and both come before Back, which is last in every bar in the tree',
   order)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

OLDBAR = bar_of(BEFORE[TPL])
OLDTAG = tags(OLDBAR)
oldprim = sorted(k for k, v in OLDTAG.items() if 'action-primary' in v)
ok(oldprim == ['doneBtn', 'genBtn', 'printBtn'],
   'CONTROL: there really were THREE primaries on the bar, and Done '
   'and Print are both on screen at once - %s' % oldprim, oldprim)
ok('{% if ingredients %}' not in OLDBAR,
   'CONTROL: and Generate List was offered whatever the page could do')
ok('{% if ingredients %}' in BEFORE[TPL],
   'CONTROL: while the two-step flow below it was ALREADY gated on '
   'exactly that condition - the fact was there, the bar just never '
   'asked it')
ok('ALV_CAN_GENERATE' not in BEFORE[TPL],
   'CONTROL: and setBar knew only which step was open')


# ==========================================================================
head('3. DRIVEN AND RENDERED - FOUR STATES, TWO WIDTHS')
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

PAGE = NOTHING = None
if django_up:
    import datetime as dt
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import (Ingredient, IngredientCategory, MealEntry,
                              MeasurementUnit, Recipe, RecipeIngredient)

    u = User.objects.create_user(username='sb2', password='x',
                                 email='sb2@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        u.user_permissions.add(Permission.objects.get(codename=cn))
    cl = Client()
    cl.force_login(u)

    WEEK = [dt.date(2026, 10, 19) + dt.timedelta(days=i) for i in range(7)]
    cat = IngredientCategory.objects.create(name='Vegetables')
    gram = MeasurementUnit.objects.create(
        name='gram', name_plural='grams', abbreviation='g',
        abbreviation_plural='g', unit_type='weight')
    URL = ('/meal_plans/shopping_list/?from=2026-10-19&to=2026-10-25')

    def plan(with_units):
        Recipe.objects.all().delete()
        Ingredient.objects.all().delete()
        MealEntry.objects.all().delete()
        names = ['Roast chicken', 'Soup for six', "Yiayia's stew"]
        recs = [Recipe.objects.create(recipe_name=n, servings=4)
                for n in names]
        ings = [Ingredient.objects.create(
            name=n, category=cat,
            default_unit=gram if with_units else None)
            for n in ('Onions', 'Carrots', 'Potatoes', 'Rice')]
        for i, r in enumerate(recs):
            for k in range(3):
                RecipeIngredient.objects.create(
                    recipe=r, ingredient=ings[(i + k) % len(ings)],
                    amount=100 + 50 * k, unit=gram)
            MealEntry.objects.create(date=WEEK[i], recipe=r, servings=4,
                                     sort_order=1, created_by=u)
        return cl.get(URL).content.decode('utf-8')

    PAGE = plan(True)
    NOTHING = plan(False)

    ok('id="step1Content"' in PAGE,
       'a plan whose ingredients HAVE a shopping unit renders step 1')
    ok('id="genBtn"' in PAGE,
       '  and the bar offers Generate List')
    ok('id="step1Content"' not in NOTHING,
       'a plan whose ingredients have NONE does not render step 1 at '
       'all - which is the state the bar never asked about')
    ok('NOT ON THIS LIST' in NOTHING,
       '  it says NOT ON THIS LIST instead')
    ok('id="genBtn"' not in NOTHING,
       '  AND THE BAR DOES NOT OFFER TO GENERATE FROM IT - the whole '
       'round, in one line')
    ok('var ALV_CAN_GENERATE = false;' in NOTHING
       and 'var ALV_CAN_GENERATE = true;' in PAGE,
       '  and the flag agrees with the markup on both pages')
    ok('Set base units' in NOTHING,
       '  leaving Set base units as the one thing there is to do')

LOCAL = '/tmp/claude-0/drive/node_modules'
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if PAGE is None or sync_playwright is None:
    skip('the renders', 'no page, or no Playwright')
else:
    FIX = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
    css = read(FIX) if os.path.isfile(FIX) else ''
    FA = '/opt/npm-tools/node_modules/@fortawesome/fontawesome-free'

    def route(r):
        url = r.request.url
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
        for k, p in (('jquery', LOCAL + '/jquery/dist/jquery.min.js'),
                     ('popper',
                      LOCAL + '/popper.js/dist/umd/popper.min.js'),
                     ('bootstrap.min.js',
                      LOCAL + '/bootstrap/dist/js/bootstrap.min.js')):
            if k in url and os.path.isfile(p):
                with open(p, 'rb') as f:
                    return r.fulfill(status=200, body=f.read(),
                                     content_type='application/javascript')
        return r.fulfill(status=200, body=b'', content_type='text/plain')

    # COUNTED OFF COMPUTED COLOUR, NOT OFF A CLASS NAME. A class is
    # what the round wrote; a fill is what Demetri sees. The two agree
    # only while the stylesheet says so, and that is the thing worth
    # asking in a browser.
    STATE = """() => {
        const bar = document.querySelector('.page-action-buttons');
        const out = [];
        bar.querySelectorAll('.btn').forEach(b => {
            const s = getComputedStyle(b);
            if (b.hasAttribute('hidden') || s.display === 'none') return;
            out.push({id: b.id || '', text: b.textContent.trim()
                        .replace(/\\s+/g, ' '), bg: s.backgroundColor});
        });
        return out;
    }"""

    def fills(rows):
        return [r['bg'] for r in rows]

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for label, width in (('desktop', 1280), ('phone', 390)):
            print('')
            pg = br.new_page(viewport={'width': width, 'height': 1200})
            pg.route(re.compile(r'^https?://'), route)
            pg.set_content(PAGE.replace(
                '<head>', '<head><base href="http://127.0.0.1/">'),
                wait_until='load')
            pg.wait_for_timeout(600)

            s1 = pg.evaluate(STATE)
            teal = [r for r in s1 if r['bg'] == 'rgb(14, 124, 139)']
            ok(len(teal) == 1 and teal[0]['id'] == 'genBtn',
               '%s STATE 1: exactly one filled control, and it is '
               'Generate List' % label, s1)

            pg.evaluate("""() => {
                document.querySelectorAll(
                    '#step1Content input[type=checkbox]').forEach(
                        c => { if (!c.checked) { c.click(); } });
            }""")
            pg.evaluate('generateShoppingList()')
            pg.wait_for_timeout(500)
            s2 = pg.evaluate(STATE)
            teal = [r for r in s2 if r['bg'] == 'rgb(14, 124, 139)']
            ok(len(teal) == 1 and teal[0]['id'] == 'doneBtn',
               '%s STATE 2: exactly one filled control, and it is Done '
               '- it was TWO before this round' % label, s2)
            printed = [r for r in s2 if r['id'] == 'printBtn']
            ok(len(printed) == 1
               and printed[0]['bg'] != 'rgb(14, 124, 139)',
               '  and Print is on screen WITHOUT the fill - a secondary',
               printed)

            pg.evaluate('goBackToReview()')
            pg.wait_for_timeout(400)
            s3 = pg.evaluate(STATE)
            ok(fills(s3) == fills(s1),
               '%s STATE 3: back on step 1, and the bar is exactly what '
               'it was' % label, (fills(s1), fills(s3)))
            ok(not [r for r in s3 if r['id'] == 'printBtn'],
               '  with Print hidden again - SL-1 still holds')
            pg.close()

            pg = br.new_page(viewport={'width': width, 'height': 1200})
            pg.route(re.compile(r'^https?://'), route)
            pg.set_content(NOTHING.replace(
                '<head>', '<head><base href="http://127.0.0.1/">'),
                wait_until='load')
            pg.wait_for_timeout(600)
            s4 = pg.evaluate(STATE)
            ok(not [r for r in s4 if r['id'] == 'genBtn'],
               '%s STATE 4: Generate List is not on the bar at all when '
               'there is nothing to generate' % label, s4)
            ok(not [r for r in s4 if r['bg'] == 'rgb(14, 124, 139)'],
               '  and no filled control is offered on a page where '
               'nothing can be done', s4)
            ok([r for r in s4 if 'Back' in r['text']],
               '  while Back is still there, so the page is not a dead '
               'end', s4)
            wide = pg.evaluate(
                '() => document.documentElement.scrollWidth')
            ok(wide <= width,
               '  and the page does not scroll sideways - %dpx' % wide,
               wide)
            pg.close()
        br.close()


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
ok(not os.path.isfile(os.path.join(ROOT, 'test_shopping_list.py') + SUFFIX),
   'SL-1/2/3 own suite is UNTOUCHED - it reads its page through '
   'as_left_by(), so it sees the pre-SB-2 text, where genBtn really did '
   'always ship visible')
ok(not os.path.isfile(os.path.join(ROOT, 'pages', 'views', 'recipes',
                                   'meal_planning.py') + SUFFIX),
   'and the view is untouched - the condition this round hangs on was '
   'already in the template')

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
ok('ALV_CAN_GENERATE' in gate, 'the sentinel is on the push gate')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_shop_bar2 as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that Done is the right primary. That is Demetri call,')
print('  made on 22 October from the rendered states, and the case')
print('  for Print was put to him beside it: step 2 verb is getting')
print('  the list into a usable form, and Done only leaves the page.')
print('')
print('  Not that no other bar in this tree has two primaries. This')
print('  one was found by rendering its states, not by a census.')
print('  Nothing counts primaries within a bar anywhere else, and a')
print('  sweep for that is its own round.')
print('')
print('  Not that state 4 is common. It needs a plan whose every')
print('  ingredient lacks a shopping unit. It is reachable, it is')
print('  reached by setting base units up badly, and the bar should')
print('  not lie about it whether or not anybody is standing there.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
