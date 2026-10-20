# -*- coding: utf-8 -*-
"""test_pick_reload.py - round RL-1, 20 Oct 2026.

THE PICKER'S RELOAD NEVER BOUND.

Demetri: "When I select a recipe in the picker, from the month view and
then say Done, the recipe doesn't show on the month view. If I refresh
the page, then it shows."

PS-1 wrote the handler and registered it while the document was still
parsing. base loads jQuery near the END of the document, so
window.jQuery was undefined, the guard returned, and nothing bound.

WHY THIS SUITE IS AN A/B AND NOT A GREP.

Both spellings of this block contain `on('hidden.bs.modal', ...)`.
Both contain the guard. Reading the file cannot tell them apart on the
thing that matters - WHEN the binding runs - so section 3 renders the
same page twice, once with each spelling, against a jQuery that
arrives LATE, exactly as base's does. One binds; one does not.

THE OLD SPELLING COMES FROM THE PATCHER'S OWN LITERAL, not from a copy
typed here, so the two can never drift apart.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One handler, in one named function, behind a
      readyState check, with the guard still on.

  2   THE CONTROL. Re-asked of the pre-round file, which binds at
      parse time.

  3   THE A/B, in a browser, with jQuery loading late.

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

import datetime as dt
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_pickreload'
ME = 'test_pick_reload.py'
PATCHER = 'apply_pick_reload.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'RL-1, 20 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
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


def claims(bundle):
    js = T.code_only_js(bundle[TPL])
    c = {}
    c['there is exactly one close handler'] = (
        js.count("on('hidden.bs.modal'") == 1)
    c['IT BINDS AFTER THE DOCUMENT IS PARSED - the finding, in one '
      'line'] = ("document.addEventListener('DOMContentLoaded', bind)"
                 in js)
    c['and it is in one named function, called from both states'] = (
        js.count('function bind()') == 1)
    c['a document already parsed is handled too'] = (
        "document.readyState === 'loading'" in js)
    # THE GUARD SURVIVES. Deleting it would also fix the bug and
    # restore the crash PS-1 fixed - a trade, not a repair.
    c['the guard is still there'] = ('!el || !window.jQuery' in js)
    c['and the reload is still conditional on a change'] = (
        'if (pickerDirty)' in js)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# THE REASON THE BUG EXISTS, asked rather than assumed. If base ever
# moves jQuery into the head this round stops being necessary, and
# somebody should be told rather than left to wonder.
_b = read(BASE)
_jq = _b.find('jquery')
ok(_jq > len(_b) * 0.5,
   'base still loads jQuery in the second half of the document, which '
   'is why a guard at parse time finds nothing',
   'at %d of %d characters' % (_jq, len(_b)))


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
held = [m for m, got in claims(BEFORE).items() if got]
ok('IT BINDS AFTER THE DOCUMENT IS PARSED - the finding, in one line'
   not in held,
   'CONTROL: before this round it bound while the document was parsing',
   'what held: %r' % (held,))
OLDJS = T.code_only_js(BEFORE[TPL])
ok("on('hidden.bs.modal'" in OLDJS,
   'CONTROL: and the handler itself was already written - it was never '
   'missing, only never registered')
ok('!el || !window.jQuery' in OLDJS,
   'CONTROL: behind the same guard, which is what silenced it')


# ==========================================================================
head('3. THE A/B, WITH jQUERY ARRIVING LATE')
# ==========================================================================
# Reading the file cannot separate these two spellings on the only
# thing that differs - WHEN the binding runs. So render the same page
# twice and ask the DOM which one ended up with a listener.
page = None
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
    from pages.models import MealEntry, Recipe
    u = User.objects.create_user(username='rl1', password='x',
                                 email='rl1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    MealEntry.objects.create(date=dt.date(2026, 10, 20), recipe=r,
                             servings=4, created_by=u)
    cl = Client()
    cl.force_login(u)
    resp = cl.get('/meal_plans/', {'view': 'month',
                                   'date': '2026-10-20'})
    if resp.status_code == 200:
        page = resp.content.decode('utf-8')
except Exception as e:
    skip('the A/B', 'Django would not start: %s'
         % str(e).split('\n')[0][:80])

if page is None:
    skip('the A/B', 'no page')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:40])

    # THE OLD SPELLING COMES FROM THE PATCHER, so the two halves of
    # this comparison cannot drift apart from the round they judge.
    import apply_pick_reload as PATCH                       # noqa: E402
    after = page
    before = page.replace(PATCH.BIND_NOW, PATCH.BIND_WAS)
    swapped = (before != after)
    ok(swapped,
       'the patcher\'s own literal was found in the served page, so the '
       'before/after pair is the round and not a paraphrase of it')

    # jQUERY ARRIVES LATE, exactly as base's does: a script tag AFTER
    # the inline block. A stub, because the question is when a handler
    # is registered and not what jQuery does with it.
    LATE = """<script>
      window.jQuery = function (el) {
        return { on: function (name, fn) {
            (el.__bound = el.__bound || []).push(name);
            return this; } };
      };
    </script></body>"""

    if sync_playwright is not None and swapped:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            bound = {}
            for label, html in (('before RL-1', before),
                                ('after RL-1', after)):
                if '</body>' not in html:
                    skip(label, 'no </body> to load jQuery before')
                    continue
                pg = br.new_page(viewport={'width': 1200, 'height': 900})
                pg.set_content(html.replace('</body>', LATE, 1),
                               wait_until='load')
                pg.wait_for_timeout(200)
                bound[label] = pg.evaluate(
                    """() => {
                        const e = document.getElementById('pickerModal');
                        return e && e.__bound ? e.__bound : [];
                    }""")
                pg.close()
            br.close()

        print('')
        for label in ('before RL-1', 'after RL-1'):
            print('  %-14s listeners bound: %r'
                  % (label, bound.get(label)))
        print('')

        ok(bound.get('before RL-1') == [],
           'CONTROL: the old spelling bound NOTHING - jQuery was not '
           'there yet and the guard returned',
           bound.get('before RL-1'))
        ok('hidden.bs.modal' in (bound.get('after RL-1') or []),
           'THE FINDING: the new spelling binds, because it waits for '
           'the document to finish parsing',
           bound.get('after RL-1'))


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_pickerstays']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose handler it re-registers - so '
       'revert takes them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
