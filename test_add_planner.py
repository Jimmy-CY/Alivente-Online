# -*- coding: utf-8 -*-
"""test_add_planner.py - round AP-1, 20 Oct 2026.

PUT A RECIPE ON A DAY WITHOUT LEAVING THE LIBRARY.

Demetri: "stay put, with a toast - Fakes Soupa added to Sat 24 Oct -
and an Undo." And: "Beside the heart on the photo."

THREE OF THIS ROUND'S FAULTS WERE INVISIBLE TO A READING, and all
three are claims here because all three were found by driving it:

    the builders read USER_CAN_EDIT_RECIPES, which the page did not
    declare - a ReferenceError on the first redraw after a search,
    taking the rest of the block with it;

    the popover borrowed the page's only csrf_token, which sits behind
    can_edit_personal - a DIFFERENT permission from the one that draws
    the icon, so somebody who may plan meals but not edit recipes got
    the icon and a 403;

    the Undo posted entry_id where remove_meal_entry reads
    meal_entry_id, so the lookup missed, the view redirected, and the
    toast SAID IT HAD REMOVED IT.

That last one is the shape this suite exists for. A control that
reports a success it did not have is worse than one that fails.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Four icons, the permission declared, one popover
      carrying its own token and its routes, three shortcuts, an Undo
      that checks.

  2   THE CONTROL. Re-asked of the pre-round files.

  3   THE ENDPOINTS, POSTED. added_id comes back and names the row;
      the label carries the weekday; and the id it hands over really
      removes when sent under the name the endpoint reads.

  4   THE POPOVER, RENDERED. Seven columns, Monday first.

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

SUFFIX = '.bak_addplanner'
ME = 'test_add_planner.py'
PATCHER = 'apply_add_planner.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'AP-1, 20 Oct 2026'

RM = os.path.join(ROOT, 'pages', 'templates', 'recipe_management.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
GATE = os.path.join(ROOT, PS1)
FILES = (RM, BASE, VIEW)
N_ICONS = 4

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


def popover(code):
    """The popover's own markup, and nothing else around it."""
    i = code.find('id="planPop"')
    if i < 0:
        return ''
    j = code.find('plan-cal-grid', i)
    k = code.find('</div>', j if j > 0 else i)
    return code[i:k if k > 0 else len(code)]


def claims(bundle):
    rm = T.code_only(bundle[RM])
    js = T.code_only_js(bundle[RM])
    bs = T.code_only_js(bundle[BASE])
    vw = T.python_code_only(bundle[VIEW], payloads=True)
    pop = popover(rm)
    c = {}
    c['FOUR ICONS, one beside each heart - the finding'] = (
        rm.count('data-plan-id=') == N_ICONS)
    # THE CONSTANT THE BUILDERS READ. Without it the first redraw
    # after a search throws and takes the block with it.
    c['the permission they test is declared'] = (
        js.count('const USER_CAN_EDIT_RECIPES') == 1)
    c['and it is the one add_meal_entry asks for'] = (
        'can_edit_recipes' in rm)
    c['one popover for the page'] = (rm.count('id="planPop"') == 1)
    # ITS OWN TOKEN, NOT SOMEBODY ELSE'S PERMISSION.
    c['IT CARRIES ITS OWN TOKEN - not one behind another '
      'permission'] = ('csrf_token' in pop)
    c['and the JavaScript reads that field'] = (
        'csrfmiddlewaretoken' in js)
    c['its routes come from the urlconf'] = (
        'data-add-url=' in pop and 'data-remove-url=' in pop)
    # SC-1, 21 Oct 2026 - TWO. Demetri: "Tonight should be Today.
    # Then let's remove This Saturday - it doesn't really add value."
    # The third button and its when() branch both went.
    c['the two shortcuts are there'] = all(
        'data-plan-when="%s"' % w in rm
        for w in ('today', 'tomorrow'))
    c['  and the third one is gone, with its branch'] = (
        'data-plan-when="saturday"' not in rm)
    c['base owns the toast'] = ('window.alvToast' in bs)
    c['and the toast sets its text as text'] = (
        'textContent' in bs.split('window.alvToast', 1)[-1][:1800])
    c['the endpoint hands back the row it made'] = (
        "payload['added_id']" in vw)
    c['AND THE UNDO CHECKS BEFORE IT CELEBRATES - the one that '
      'lied'] = ('r.redirected' in js)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# THE UNDO POSTS WHAT THE ENDPOINT READS, asked across both files.
VW = T.python_code_only(NOW[VIEW], payloads=True)
seg = VW[VW.index('def remove_meal_entry'):]
seg = seg[:seg.index('return redirect')]
wanted = [w for w in
          re.findall(r"request\.POST\.get\('([a-z_]+)'\)", seg)
          if w != 'json']
ok(bool(wanted) and wanted[0] in T.code_only_js(NOW[RM]),
   'the Undo posts %r, which is what remove_meal_entry reads'
   % (wanted[0] if wanted else '?'), wanted)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok('FOUR ICONS, one beside each heart - the finding' not in held,
   'CONTROL: before this round no card offered the planner',
   'what held: %r' % (held,))
ok('base owns the toast' not in held,
   'CONTROL: and base had no toast at all - which is why this could '
   'not be done with django messages')
OLDRM = T.code_only(BEFORE[RM])
ok(OLDRM.count('toggleFavourite(')
   - len(re.findall(r'function toggleFavourite\(', OLDRM)) == N_ICONS,
   'CONTROL: the four hearts were already there - counted without '
   'the DECLARATION, which made it five the first time')


# ==========================================================================
head('3. THE ENDPOINTS, POSTED')
# ==========================================================================
import datetime as dt                                       # noqa: E402
sent = {}
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
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from django.urls import reverse
    from pages.models import MealEntry, Recipe
    u = User.objects.create_user(username='ap1', password='x',
                                 email='ap1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    cl = Client()
    cl.force_login(u)
    # SATURDAY THE 24th, which is the day in his own sentence.
    resp = cl.post(reverse('add_meal_entry'),
                   {'recipe_id': r.recipe_id, 'date': '2026-10-24',
                    'json': '1'})
    sent['add'] = (resp.status_code,
                   resp.json() if resp.status_code == 200 else {})
    if sent['add'][1].get('added_id'):
        before_n = MealEntry.objects.count()
        rm_resp = cl.post(
            reverse('remove_meal_entry'),
            {wanted[0]: sent['add'][1]['added_id'], 'json': '1'})
        sent['remove'] = (rm_resp.status_code,
                          before_n, MealEntry.objects.count())
except Exception as e:
    skip('the posted checks',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if 'add' not in sent:
    skip('the endpoints', 'nothing was posted')
else:
    code, data = sent['add']
    print('')
    print('  add   -> %s  added_id=%s  added_label=%r'
          % (code, data.get('added_id'), data.get('added_label')))
    if 'remove' in sent:
        print('  undo  -> %s  rows %d -> %d'
              % sent['remove'])
    print('')
    ok(code == 200, 'the add answers with JSON', code)
    ok(bool(data.get('added_id')),
       'and names the row it just made - an Undo has something to '
       'point at', data)
    # THE WEEKDAY, which is the half of his sentence that says
    # whether you meant it: "added to Sat 24 Oct".
    ok((data.get('added_label') or '').startswith('Sat'),
       'the label carries the weekday - "%s"'
       % data.get('added_label'), data.get('added_label'))
    ok('24 Oct' in (data.get('added_label') or ''),
       '  and the day, in the house spelling')
    if 'remove' in sent:
        rc, b, a = sent['remove']
        ok(rc == 200,
           'the Undo is answered, not redirected - a redirect is what '
           'the first spelling got, and it was reported as a success',
           rc)
        ok(a == b - 1,
           'AND THE ROW IS REALLY GONE - %d became %d' % (b, a))


# ==========================================================================
head('4. THE POPOVER, RENDERED')
# ==========================================================================
page = None
try:
    resp = cl.get(reverse('recipe_management'))
    if resp.status_code == 200:
        page = resp.content.decode('utf-8')
except Exception as e:
    skip('the rendered checks', str(e)[:60])

if page is None:
    skip('the popover', 'no page')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1400, 'height': 1000})
            pg.set_content(page, wait_until='load')
            n_icon = pg.evaluate(
                "() => document.querySelectorAll('[data-plan-id]').length")
            pg.evaluate(
                "() => document.querySelector('[data-plan-id]').click()")
            pg.wait_for_timeout(250)
            seen = pg.evaluate("""() => {
                const p = document.getElementById('planPop');
                const dow = [...document.querySelectorAll('.plan-cal-dow')]
                    .map(e => e.textContent);
                return {
                    open: !!p && !p.hidden,
                    dow: dow,
                    days: document.querySelectorAll('[data-plan-date]').length,
                    quick: [...document.querySelectorAll('.plan-quick')]
                        .map(e => e.textContent),
                    token: !!p && !!p.querySelector('[name=csrfmiddlewaretoken]')
                };
            }""")
            br.close()

        print('')
        print('  icons %d   open %s   columns %d   days %d'
              % (n_icon, seen['open'], len(seen['dow']), seen['days']))
        print('  shortcuts %s' % (seen['quick'],))
        print('')
        ok(n_icon > 0, 'the icons are on the page', n_icon)
        ok(seen['open'], 'pressing one opens the popover')
        ok(len(seen['dow']) == 7,
           'the month is seven columns', len(seen['dow']))
        # MONDAY FIRST, like every other calendar in this application.
        ok(seen['dow'][:1] == ['M'],
           '  and Monday is the first of them', seen['dow'])
        ok(seen['days'] >= 28,
           'a month of days is drawn', seen['days'])
        ok(len(seen['quick']) == 2,
           'with the two shortcuts above it - SC-1, 21 Oct 2026, '
           'took This Saturday away', seen['quick'])
        ok(seen['token'],
           'and the popover carries its own token, so it does not '
           'need somebody else\'s permission to post')


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_quicklook']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose cards it edits - so revert takes '
       'them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_add_planner as PATCH                           # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
