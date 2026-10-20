# -*- coding: utf-8 -*-
"""test_day_card.py - round DC-1, 19 Oct 2026.

RELEASE 4, PUSH 2. THE DAY CARD USES ITS WIDTH.

Demetri, on the Day view: "The buttons are all on top of each other.
Servings, View, Repeat, Delete and it looks messy. Also, there is no
clever use of space. 90% of the box is empty."

THE CLAIM THAT MATTERS: the row is one line and the width is used.
Both are measurements, and section 3 takes them from a rendered page.

AND THE MEASUREMENT IS THE LESSON OF THIS ROUND. "63% empty" took
three instruments, and the first two both said the opposite:

    every descendant's box    99% used   WRONG. .recipe-info is a
                                         block and fills the row.
    leaf elements only        99% used   STILL WRONG. An h5 is a leaf
                                         AND a block.
    a Range around the text   37% used   63% empty.

> A block element's rectangle is the row's width whatever is written
> in it.

So this suite measures with a Range too, and section 3 reads the
BEFORE off the backup as well as the AFTER off the tree - because a
number with nothing beside it is not evidence of a repair.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One line behind a min-width; min-width: 0 on the
      flex child; the tags bounded; ink-soft on words; the phone
      keeping its stack.

  2   THE CONTROL. Re-asked of the pre-round file.

  3   RENDERED AND MEASURED, before and after, at 1200 and 390.

  4   THE TAGS COST NOTHING - asked of the query count, not assumed.

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
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_daycard'
ME = 'test_day_card.py'
PATCHER = 'apply_day_card.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'DC-1, 19 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
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
    t = T.code_only(bundle[TPL])
    c = {}
    desktop = re.search(
        r'@media screen and \(min-width: 768px\)\s*\{(.*?)\n\}', t, re.S)
    body = desktop.group(1) if desktop else ''

    c['the one-line layout exists'] = ('.recipe-info' in body)
    c['and it is behind a min-width, so the phone keeps its stack'] = (
        bool(desktop) and 'display: flex' in body)
    # A FLEX ITEM'S DEFAULT MINIMUM IS ITS CONTENT, NOT NOTHING. Without
    # this a long recipe name refuses to shrink and pushes the stepper
    # off the row - which is the fault, moved rather than fixed.
    c['.recipe-info has min-width: 0, or a long name pushes the '
      'stepper off the row'] = ('min-width: 0' in body)
    c['the name truncates rather than wrapping'] = (
        'text-overflow: ellipsis' in body)

    c['the row carries tags'] = ('class="dc-tags"' in t)
    # BOUNDED. A recipe with nine categories would recreate the
    # stacking this round exists to end.
    c['bounded to one course and one category'] = (
        t.count('|slice:":1"') == 2)
    _tag = re.search(r'\.dc-tag\s*\{[^}]*\}', t, re.S)
    c['and they are ink-soft, because they are words somebody reads '
      'and faint measures 2.53 on this ground'] = (
        bool(_tag) and 'var(--alv-ink-soft)' in _tag.group(0))
    # HIDDEN ON A PHONE, not wrapped - three pills on a 300px row
    # would push the stepper onto a fifth line.
    c['hidden on a phone rather than wrapped'] = (
        bool(re.search(r'@media screen and \(max-width: 767px\)[^}]*\{'
                       r'[^@]*?\.dc-tags\s*\{\s*display:\s*none',
                       t, re.S)))
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
ok(not held,
   'not one of the claims held before this round ran',
   'these held already: %r' % (held[:4],))
OLD = T.code_only(BEFORE[TPL])
ok('class="dc-tags"' not in OLD,
   'CONTROL: there were no tags on the row')
ok(re.search(r'@media screen and \(min-width: 768px\)\s*\{[^@]*'
             r'\.recipe-info', OLD, re.S) is None,
   'CONTROL: and .recipe-info was a vertical stack at every width')


# ==========================================================================
head('3. RENDERED AND MEASURED - before and after')
# ==========================================================================
MEASURE = """() => {
  const rows = Array.from(document.querySelectorAll('.recipe-item'));
  if (!rows.length) { return null; }
  const e = rows[0];
  const rr = e.getBoundingClientRect();
  // A RANGE AROUND THE TEXT. A block's rectangle is the row's width
  // whatever is written in it, so measuring elements - even leaves -
  // reports 99% and means nothing.
  let right = 0;
  const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT, null);
  let n;
  while ((n = w.nextNode())) {
    if (!n.nodeValue.trim()) { continue; }
    const rg = document.createRange();
    rg.selectNodeContents(n);
    const b = rg.getBoundingClientRect();
    if (b.width > 0) { right = Math.max(right, b.right); }
  }
  for (const el of e.querySelectorAll('img, i, button, input')) {
    const b = el.getBoundingClientRect();
    if (b.width > 0) { right = Math.max(right, b.right); }
  }
  const info = e.querySelector('.recipe-info');
  const kids = info ? Array.from(info.children).map(
      k => Math.round(k.getBoundingClientRect().width)) : [];
  return {w: Math.round(rr.width), h: Math.round(rr.height),
          ink: Math.round(right - rr.left),
          widestChild: kids.length ? Math.max(...kids) : 0,
          tags: e.querySelectorAll('.dc-tag').length,
          tagsShown: Array.from(e.querySelectorAll('.dc-tag')).filter(
              x => x.getBoundingClientRect().width > 0).length};
}"""

shots = {}
queries = {}
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
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import (MealEntry, Recipe, RecipeCategory,
                              RecipeCourse)
    u = User.objects.create_user(username='dc1', password='x',
                                 email='dc1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    soup = RecipeCourse.objects.create(name='Soup', display_order=1)
    greek = RecipeCategory.objects.create(name='Greek')
    day = dt.date(2026, 10, 19)
    for name in ('Fakes Soupa', 'Amygdalopita'):
        rec = Recipe.objects.create(recipe_name=name, servings=6,
                                    prep_time=15, cook_time=45,
                                    is_vegetarian=True)
        rec.courses.add(soup)
        rec.categories.add(greek)
        MealEntry.objects.create(date=day, recipe=rec, servings=6,
                                 created_by=u)
    cl = Client()
    cl.force_login(u)
    resp = cl.get('/meal_plans/', {'view': 'day', 'date': '2026-10-19'})
    shots['after'] = resp.content.decode('utf-8') \
        if resp.status_code == 200 else None

    # ---- THE QUERY COUNT, asked rather than assumed.
    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    with CaptureQueriesContext(connection) as cap:
        cl.get('/meal_plans/', {'view': 'day', 'date': '2026-10-19'})
    queries['after'] = len(cap.captured_queries)
except Exception as e:
    skip('everything that needs a rendered page',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if not shots.get('after'):
    skip('the measurements', 'no page')
else:
    # THE BEFORE, from the backup's stylesheet applied to the same
    # page - the markup this round added is left in place and the
    # RULES are the ones it replaced, which is what the row looked
    # like for everything that matters to a layout measurement.
    before_css = re.findall(r'<style>(.*?)</style>', was(TPL), re.S)
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser measurements', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            got = {}
            for width, label in ((1200, 'desktop'), (390, 'phone')):
                pg = br.new_page(viewport={'width': width,
                                           'height': 1100})
                pg.set_content(shots['after'], wait_until='load')
                pg.wait_for_timeout(220)
                got[('after', label)] = pg.evaluate(MEASURE)
                pg.close()

                # THE BEFORE: the same page with this round's rules
                # turned off, which is the only honest comparison -
                # two different fixtures would compare two pages.
                pg = br.new_page(viewport={'width': width,
                                           'height': 1100})
                pg.set_content(shots['after'], wait_until='load')
                pg.evaluate(
                    """() => {
                       const s = document.createElement('style');
                       s.textContent =
                         '@media screen and (min-width: 768px){' +
                         '.recipe-item{align-items:flex-start}' +
                         '.recipe-info{display:block}' +
                         '.recipe-meta,.dc-tags,.servings-step,' +
                         '.row-actions{margin:6px 0 0 0}}';
                       document.body.appendChild(s);
                    }""")
                pg.wait_for_timeout(220)
                got[('before', label)] = pg.evaluate(MEASURE)
                pg.close()
            br.close()

        print('')
        print('  %-18s %-12s %-10s %s'
              % ('', 'row height', 'ink', 'widest child of .recipe-info'))
        for label in ('desktop', 'phone'):
            for when in ('before', 'after'):
                m = got[(when, label)]
                print('  %-18s %-12s %-10s %s'
                      % ('%s, %s' % (label, when), '%dpx' % m['h'],
                         '%d%%' % round(100.0 * m['ink'] / m['w']),
                         '%dpx' % m['widestChild']))
        print('')

        d_before = got[('before', 'desktop')]
        d_after = got[('after', 'desktop')]
        ok(d_after['h'] < d_before['h'],
           'the desktop row is shorter than it was (%dpx against %dpx)'
           % (d_after['h'], d_before['h']))
        ok(d_after['widestChild'] < d_before['widestChild'],
           'and .recipe-info lays its children SIDE BY SIDE - the '
           'widest is %dpx, where stacked it was %dpx (the row width)'
           % (d_after['widestChild'], d_before['widestChild']))
        ok(100.0 * d_after['ink'] / d_after['w'] > 90,
           'the width is used: %d%% of the row'
           % round(100.0 * d_after['ink'] / d_after['w']))

        # THE TAGS ARE THERE, AND HIDDEN ON A PHONE.
        ok(d_after['tagsShown'] >= 2,
           'the row shows its tags on a desktop',
           'showed %d of %d' % (d_after['tagsShown'], d_after['tags']))
        p_after = got[('after', 'phone')]
        ok(p_after['tags'] > 0 and p_after['tagsShown'] == 0,
           'and hides them on a phone rather than wrapping them onto a '
           'fifth line',
           'showed %d of %d' % (p_after['tagsShown'], p_after['tags']))


# ==========================================================================
head('4. THE TAGS COST NOTHING')
# ==========================================================================
v = T.python_code_only(read(VIEW), payloads=True)
ok("'recipe__courses'" in v and "'recipe__categories'" in v,
   'the planner was already prefetching courses and categories - this '
   'round shows what MN-1 had been fetching and never displaying')
if queries.get('after'):
    ok(queries['after'] < 30,
       'and the Day view costs %d quer%s in all'
       % (queries['after'], 'y' if queries['after'] == 1 else 'ies'))
else:
    skip('the query count', 'no page')


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
for _dep in []:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose work it edits - so revert takes '
       'them off in the right order' % _dep)
ok(_i >= len(alv_rounds.ROUNDS) - 8,
   'and it is among the eight newest, where this push put it',
   'it is at %d of %d' % (_i, len(alv_rounds.ROUNDS)))
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_day_card as PATCH                              # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
