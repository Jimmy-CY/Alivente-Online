# -*- coding: utf-8 -*-
"""test_chip_pill.py - round CL-1, 20 Oct 2026.

A MEAL IN THE CALENDAR LOOKS LIKE A CHIP AGAIN.

Demetri: "The recipes aren't displayed nicely, like they were before.
They were like pills before." And then: "But shouldn't they be like
pills?? not just words with a coloured background?"

RD-2 made the chips <button>s and reset them in ITS OWN <style>, which
is a LATER stylesheet than the one holding the chip. At equal
specificity the later sheet wins, so `background: transparent`,
`border: 0` and `font: inherit` beat the chip's fill, its bar and -
because `font` is a shorthand - its 11px type. What was left was 16px
plain text.

WHY THIS SUITE RENDERS.

Every declaration CL-1 cares about was PRESENT in the file before this
round and beaten in the browser. A suite that greps for
`background: var(--alv-accent-soft)` passes against the broken tree.
So section 3 reads getComputedStyle and nothing else.

THE CLUE THAT FOUND IT is a claim here too: notes and leftovers kept
their fill, because `.month-chip.is-note` is TWO classes and outranks
the reset. Any future reset that reaches further will break the plain
chip first and the other two never - so the suite checks all three.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Both chips are pills with an edge; the reset names
      only what a <button> needs.

  2   THE CONTROL. Re-asked of the pre-round file, where the reset
      names four things the chip owns.

  3   THE THREE CHIPS, RENDERED - fill, radius and type size.

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

SUFFIX = '.bak_chippill'
ME = 'test_chip_pill.py'
PATCHER = 'apply_chip_pill.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'CL-1, 20 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
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


def reset_body(code):
    """RD-2's reset, its own body and nothing else.

    ASKED OF THE RULE, NOT OF THE FILE. `background` appears about
    ninety times in this stylesheet; the question is whether THIS rule
    names it, because this rule is the one that wins.
    """
    i = code.find('.month-chip, .week-chip {')
    if i < 0:
        return None
    return code[i:code.index('}', i)]


def claims(bundle):
    code = T.code_only(bundle[TPL])
    body = reset_body(code)
    c = {}
    c['both chips are pills'] = (
        code.count('border-radius: 999px') == 2)
    c['and both carry an edge, so they read on a tinted row'] = (
        code.count('border: 1px solid var(--alv-accent-line)') == 2)
    c['THE RESET NO LONGER SETS THE FILL - the finding, in one line'] = (
        body is not None and 'background' not in body)
    c['nor the type, which a shorthand took with it'] = (
        body is not None and 'font:' not in body)
    c['nor the width, so a pill hugs its word'] = (
        body is not None and 'width:' not in body)
    c['nor the border, which the pill owns now'] = (
        body is not None and 'border' not in body)
    c['it still says a chip is pressable'] = (
        body is not None and 'cursor: pointer' in body)
    c['the left bar is gone with the flat tag'] = (
        'border-left: 2px solid var(--alv-accent)' not in code)
    # THE THREE COLOURS ARE THE VOCABULARY and this round changes only
    # the shape. A round that made them pills and lost the colours
    # would pass everything above.
    c['a recipe, a note and a leftover still differ'] = all(
        code.count(tok) >= 2 for tok in
        ('var(--alv-accent-soft)', 'var(--alv-warn-soft)',
         'var(--alv-surface-deep)'))
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
held = [m for m, got in claims(BEFORE).items() if got]
ok('THE RESET NO LONGER SETS THE FILL - the finding, in one line'
   not in held,
   'CONTROL: before this round the reset DID set the fill',
   'what held: %r' % (held,))

OLD = T.code_only(BEFORE[TPL])
OLDBODY = reset_body(OLD)
ok(OLDBODY is not None and 'font: inherit' in OLDBODY,
   'CONTROL: and it used the font SHORTHAND, which is why 11px chips '
   'rendered at 16px')
ok('border-radius: 3px' in OLD,
   'CONTROL: and the chip was a 3px flat tag, not a pill')
# THE RESET REALLY DID COME LAST. If it had sat before the chip rule
# none of this would have happened, and the round would be pointless.
ok(OLD.index('.month-chip, .week-chip {') > OLD.index('.month-chip {'),
   'CONTROL: the reset sat AFTER the rule it beat')


# ==========================================================================
head('3. THE THREE CHIPS, RENDERED')
# ==========================================================================
page = {}
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
    u = User.objects.create_user(username='cl1', password='x',
                                 email='cl1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    p = MealEntry.objects.create(date=dt.date(2026, 10, 20), recipe=r,
                                 servings=4, created_by=u)
    MealEntry.objects.create(date=dt.date(2026, 10, 21), note='Eat out',
                             servings=2, created_by=u)
    MealEntry.objects.create(date=dt.date(2026, 10, 22), recipe=r,
                             servings=2, leftover_of=p, created_by=u)
    cl = Client()
    cl.force_login(u)
    for view in ('month', 'week'):
        resp = cl.get('/meal_plans/', {'view': view,
                                       'date': '2026-10-20'})
        if resp.status_code == 200:
            page[view] = resp.content.decode('utf-8')
except Exception as e:
    skip('the rendered checks',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if not page:
    skip('the chips', 'no page')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        PROBE = """(sel) => {
            const e = document.querySelector(sel);
            if (!e) return null;
            const s = getComputedStyle(e);
            return {bg: s.backgroundColor, r: s.borderTopLeftRadius,
                    fs: s.fontSize, bw: s.borderTopWidth,
                    w: Math.round(e.getBoundingClientRect().width),
                    pw: Math.round(
                        e.parentElement.getBoundingClientRect().width)};
        }"""
        KINDS = (('a recipe', ':not(.is-note):not(.is-leftover)'),
                 ('a note', '.is-note'),
                 ('a leftover', '.is-leftover'))
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            seen = {}
            for view, html in page.items():
                pg = br.new_page(viewport={'width': 1900, 'height': 950})
                pg.set_content(html, wait_until='load')
                for label, extra in KINDS:
                    seen[(view, label)] = pg.evaluate(
                        PROBE, '.%s-chip%s' % (view, extra))
                pg.close()
            br.close()

        print('')
        print('  %-7s %-12s %-22s %-9s %-7s %s'
              % ('view', 'kind', 'fill', 'radius', 'type', 'width'))
        for key, d in sorted(seen.items()):
            if d:
                print('  %-7s %-12s %-22s %-9s %-7s %d of %d'
                      % (key[0], key[1], d['bg'], d['r'], d['fs'],
                         d['w'], d['pw']))
        print('')

        for (view, label), d in sorted(seen.items()):
            if not d:
                skip('%s %s' % (view, label), 'not on this page')
                continue
            ok(d['bg'] != 'rgba(0, 0, 0, 0)',
               '%s: %s has a fill - not bare words' % (view, label),
               d['bg'])
            ok(d['r'] == '999px',
               '%s: %s is a pill' % (view, label), d['r'])
            ok(d['fs'] == '11px',
               '%s: %s is 11px, not the inherited 16' % (view, label),
               d['fs'])
            ok(d['bw'] == '1px',
               '%s: %s has its edge' % (view, label), d['bw'])
            # IT HUGS ITS WORD. A full-width lozenge is not a pill, and
            # `width: 100%` in the reset is what made it one.
            ok(d['w'] < d['pw'],
               '%s: %s hugs its word rather than filling the column'
               % (view, label), '%d of %d' % (d['w'], d['pw']))

        # AND THE THREE ARE STILL TOLD APART BY COLOUR.
        fills = set(d['bg'] for (v, _l), d in seen.items()
                    if d and v == 'week')
        ok(len(fills) == 3,
           'the three kinds still have three different fills',
           sorted(fills))


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_chipmenu', '.bak_datebar']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose work it edits - so revert takes '
       'them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_chip_pill as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
