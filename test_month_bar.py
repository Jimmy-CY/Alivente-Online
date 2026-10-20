# -*- coding: utf-8 -*-
"""test_month_bar.py - round MB-2, 19 Oct 2026.

RELEASE 4, PUSH 2. THE DATE BAR IS A BAR.

Demetri, on the live planner: "I don't like the way it displays
October 2026, the left and right arrow and the Today button."

THE CLAIM THAT MATTERS: the navigation is no longer louder than the
thing it navigates. That is a measurement, not an opinion, and
section 3 takes it from a rendered page:

    before    switcher 32px    arrows 44px    title 17px
    after     switcher 32px    arrows 36px    title 20px

The arrows were never small. They were the biggest things in the
header - three identical 44px boxes over a 17px label, with "Today",
an ACTION, dressed as a third direction.

AND IT IS celebration_calendar's SHAPE. That screen - the other month
grid in this project - has always put the period in the middle as a
heading with the navigation at the ends on a padded surface. MV-2
built a different bar without looking. Section 1 asks whether this
round adopted it rather than inventing a fourth.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Three Today buttons, each OUTSIDE its navigation
      group; the bar joined to what it heads; the phone back at 44px.

  2   THE CONTROL. Every claim re-asked of the pre-round file, where
      Today sits between the arrows wearing the same box.

  3   RENDERED, at 1200 and 390, in all three views - because the
      same three classes dress the Week and Day headers and a bar
      that is a bar in one view only is a new inconsistency.

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

SUFFIX = '.bak_monthbar'
ME = 'test_month_bar.py'
PATCHER = 'apply_month_bar.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MB-2, 19 Oct 2026'
N_TODAY = 3

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
CAL = os.path.join(ROOT, 'pages', 'templates',
                   'celebration_calendar.html')
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

    c['each of the three views has a Today marked as an action'] = (
        t.count('week-nav-btn is-today') == N_TODAY)
    # ASKED OF THE GROUP, not of the file. A page HAVING is-today and
    # the button being OUTSIDE .week-nav are different facts, and a
    # Today still inside it would be flexed with the arrows and land
    # back in the middle - which is the thing he objected to.
    # ANCHORED TO ITS SUBJECT. "None of them is inside .week-nav" is
    # trivially true of a file with no is-today in it at all, so this
    # passed against the pre-round template. FOURTH TIME in this push -
    # RD-1 had three, RD-2 had one. A claim that something is not
    # somewhere has to establish that the something EXISTS.
    c['and not one of them is still inside .week-nav'] = (
        t.count('week-nav-btn is-today') == N_TODAY and not any(
            'is-today' in block for block in
            re.findall(r'<div class="week-nav">(.*?)</div>', t, re.S)))
      # THE MONTH HEADER ONLY. The Week and Day header already sits
    # inside .week-detail-panel with its own tinted surface and bottom
    # border - the first cut of this round gave it a second skin and
    # the rendered measurement refused it.
    c['the MONTH bar has a surface of its own'] = (
        bool(re.search(r'\.month-header\s*\{[^}]*'
                       r'background:\s*var\(--alv-paper\)', t, re.S)))
    c['joined to the grid, so the month is its heading rather than a '
      'label above it'] = (
        bool(re.search(r'\.month-header\s*\{[^}]*border-bottom:\s*0',
                       t, re.S)))
    # ANCHORED, for the same reason: the combined selector did not
    # exist before this round either.
    c['and the Week and Day header is left alone, because it already '
      'had one'] = (
        bool(re.search(r'\.month-header\s*\{[^}]*'
                       r'background:\s*var\(--alv-paper\)', t, re.S))
        and not re.search(
            r'\.month-header,\s*\n\s*\.week-detail-header', t))
    # THE LAST RULE WINS. Asked of the last .week-title in the file,
    # not of any of them: the first cut added a 20px rule a thousand
    # lines above the 17px one and lost silently.
    _titles = re.findall(r'\.week-title\s*\{[^}]*\}', t, re.S)
    c['the period is the heading, centred, in the rule that wins'] = (
        bool(_titles) and 'text-align: center' in _titles[0]
        and 'font-size: 20px' in _titles[0])
    c['the arrows are quieter than the 44px they were'] = (
        bool(re.search(r'\.week-nav-btn\s*\{[^}]*min-width:\s*36px',
                       t, re.S)))
    # A THUMB IS THE SAME SIZE AT EVERY WIDTH.
    # THE PHONE'S 44px IS NOT ASKED HERE - IT IS MEASURED.
    #
    # Two spellings of this as a source claim were wrong. `split` on
    # the media marker does not give the media BLOCK, it gives
    # everything to the end of the file, so the base rule's own
    # min-width: 44px answered yes before this round ran. Counting
    # braces to find the real block would be a parser, badly.
    #
    # Section 3 renders the page at 390px and reads the arrow's
    # height off the box. That is the claim, and it is a better one:
    # it is true of what the browser does rather than of what the
    # stylesheet says.
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# A STANDING PROPERTY, NOT ONE OF THIS ROUND'S CLAIMS. MV-3 made every
# query on this page name a media type; this round must not undo it,
# but it did not establish it either, so it does not belong in the set
# the control re-asks.
ok('@media (max-width' not in T.code_only(NOW[TPL]),
   'no bare max-width clause survives - one would match print, the '
   '21 Sep print-leak round')

# AND IT IS THE SHAPE THE APPLICATION ALREADY HAD. Asked of
# celebration_calendar rather than asserted in a comment.
if os.path.isfile(CAL):
    cal = T.code_only(read(CAL))
    ok(bool(re.search(r'\.calendar-navigation\s*\{[^}]*'
                      r'justify-content:\s*space-between', cal, re.S)),
       'CONTROL: celebration_calendar really does put its navigation '
       'at the ends')
    ok(bool(re.search(r'\.calendar-navigation h3\s*\{[^}]*'
                      r'text-align:\s*center', cal, re.S)),
       'and its period in the middle as a heading - which is the shape '
       'MV-2 invented a different one instead of')
else:
    skip('the celebration_calendar comparison', 'file not found')


# ==========================================================================
head('2. THE CONTROL - every claim re-asked of the pre-round file')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held,
   'not one of the claims held before this round ran',
   'these held already: %r' % (held[:4],))

OLD = T.code_only(BEFORE[TPL])
ok(OLD.count('class="week-nav-btn"') >= 9,
   'CONTROL: there really were three arrows and a Today in each of '
   'three views', 'found %d' % OLD.count('class="week-nav-btn"'))
ok(any('Today' in block for block in
       re.findall(r'<div class="week-nav">(.*?)</div>', OLD, re.S)),
   'CONTROL: and Today sat INSIDE the navigation group, wearing the '
   'same box as the arrows')
ok(bool(re.search(r'\.week-nav-btn\s*\{[^}]*min-width:\s*44px',
                  OLD, re.S)),
   'CONTROL: at 44px, which is 12px taller than the switcher above it')


# ==========================================================================
head('3. RENDERED - the bar against the switcher it sits under')
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
    u = User.objects.create_user(username='mb2', password='x',
                                 email='mb2@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    MealEntry.objects.create(date=dt.date(2026, 10, 21), recipe=r,
                             servings=4, created_by=u)
    cl = Client()
    cl.force_login(u)
    for view in ('month', 'week', 'day'):
        resp = cl.get('/meal_plans/', {'view': view,
                                       'date': '2026-10-19'})
        if resp.status_code == 200:
            page[view] = resp.content.decode('utf-8')
except Exception as e:
    skip('everything that needs a rendered page',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if not page:
    skip('the measurements', 'no page to render')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser measurements', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        MEASURE = """() => {
          const g = (s) => { const e = document.querySelector(s);
            if (!e) { return null; }
            const r = e.getBoundingClientRect();
            return {w: Math.round(r.width), h: Math.round(r.height),
                    top: Math.round(r.top), bottom: Math.round(r.bottom),
                    font: parseInt(getComputedStyle(e).fontSize, 10)}; };
          const bar = g('.month-header') || g('.week-detail-header');
          const grid = g('.month-grid') || g('.week-grid')
                       || g('.day-detail');
          return {seg: g('.alv-seg'), btn: g('.week-nav-btn'),
                  title: g('.week-title'), bar: bar, grid: grid,
                  today: g('.week-nav-btn.is-today')};
        }"""
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            for width, wlabel in ((1200, 'desktop'), (390, 'phone')):
                for view, html in page.items():
                    pg = br.new_page(
                        viewport={'width': width, 'height': 1000})
                    pg.set_content(html, wait_until='load')
                    pg.wait_for_timeout(180)
                    m = pg.evaluate(MEASURE)
                    pg.close()
                    tag = '%s/%s' % (view, wlabel)

                    ok(m['today'] is not None,
                       '%s: Today is on the page as an action' % tag)

                    if wlabel == 'desktop':
                        # THE WHOLE FINDING, AS A NUMBER. The arrows
                        # must not out-shout the switcher any more.
                        ok(m['btn']['h'] <= m['seg']['h'] + 6,
                           '%s: the arrows (%spx) no longer tower over '
                           'the switcher (%spx)'
                           % (tag, m['btn']['h'], m['seg']['h']))
                        ok(m['title']['font'] >= 18,
                           '%s: and the period is a heading at %spx, '
                           'not a label at 17'
                           % (tag, m['title']['font']))
                    else:
                        # A THUMB IS THE SAME SIZE AT EVERY WIDTH.
                        ok(m['btn']['h'] >= 44,
                           '%s: the arrows are %spx - still a thumb '
                           'target' % (tag, m['btn']['h']))

                    # JOINED - MONTH ONLY, and measured against the
                    # grid rather than against whatever happened to be
                    # next. In Week the seven-column grid is
                    # display:none on a phone, and measuring a hidden
                    # box reported a 637px gap.
                    if view == 'month' and m['grid'] \
                            and m['grid']['h'] > 0:
                        gap = m['grid']['top'] - m['bar']['bottom']
                        ok(abs(gap) <= 2,
                           '%s: the bar meets what it heads (%spx gap)'
                           % (tag, gap))
            br.close()


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
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
ok('week-nav-btn is-today' in gate, 'the gate pins Today as an action')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_month_bar as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
