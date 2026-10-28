# -*- coding: utf-8 -*-
"""test_week_fill.py - round WF-1, 21 Oct 2026.

THE WEEK BAND NEEDED A FILL, AND THERE WAS ROOM FOR ONE AFTER ALL.

    "I don't like the way that the current week is highlighted in the
     Month View. It needs a colour fill."

WT-1 FOUND THE FAULT THIS MORNING AND IT STANDS: the band filled with
`--alv-accent-soft`, the token `.month-chip` fills ITSELF with, so a
meal on the selected week was the pill's 1px border and nothing else.

WHAT IT GOT WRONG WAS THE SEARCH. It measured two candidates for a
fourth fill, found both too close to something, and wrote down that
there was no room. base carries ten more pale tints in the TAG
palette - sky, moss, clay, slate, plum - which exist to be decorative
and carry no status meaning at all, unlike good, warn or bad. None of
them had been looked at.

TWO IS NOT A SEARCH. Section 3 asks all thirteen, against all five
fills already on that grid, and prints the table - so the next round
proposing a sixth fill inherits a measurement instead of a sentence.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The band fills with moss, keeps its accent rule,
      and nothing else on the grid moved.

  2   THE CONTROL. Re-asked of .bak_weekfill, where it was paper.

  3   THE NUMBERS. Thirteen candidates, five existing fills, worst
      case each. Moss wins and the two WT-1 measured really do fail -
      that half of WT-1 was right.

  4   RENDERED, AND SAMPLED OFF THE SCREEN. A real month view, and
      the colours read out of the PIXELS rather than the stylesheet:
      the band, and a meal, a note and a leftover sitting on it. A
      token that resolves is not the same as a pixel that paints.

  5   WT-1's OWN SUITE, RUN. This round corrects two of its claims in
      the same patcher; a claim moved is a claim that has to still fit.

  6   Scope, registration and the gate.

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
import math
import os
import re
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_weekfill'
ME = 'test_week_fill.py'
PATCHER = 'apply_week_fill.py'
PS1 = 'Push-PendingChanges.ps1'
BAND = 'test_week_band.py'
MARK = 'WF-1, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL,)

# dE under about 2 is the threshold a trained eye can just detect.
# A pill on a band needs to clear it with room to spare.
VISIBLE = 2.0
NEW = '--alv-tag-moss-soft'
# WHAT IS ALREADY PAINTED ON THAT GRID. A candidate is only as good
# as its nearest collision, so all five are asked of every candidate.
ON_GRID = (('the cell', '--alv-paper'),
           ('out of month', '--alv-surface'),
           ('MEAL pill', '--alv-accent-soft'),
           ('NOTE pill', '--alv-warn-soft'),
           ('LEFTOVER pill', '--alv-surface-deep'))
CANDIDATES = ('--alv-tag-moss-soft', '--alv-tag-clay-soft',
              '--alv-tag-plum-soft', '--alv-tag-slate-soft',
              '--alv-tag-sky-soft', '--alv-good-soft', '--alv-warn-soft',
              '--alv-spice-soft', '--alv-bad-soft', '--alv-neutral-soft',
              '--alv-surface-deep', '--alv-surface', '--alv-accent-soft')
# THE THREE THAT CARRY A MEANING. A band is not a status, so a status
# colour on it would be the application telling you something it does
# not mean.
MEANS = {'--alv-good-soft': 'healthy / on time',
         '--alv-warn-soft': 'needs attention',
         '--alv-bad-soft': 'overdue / failed',
         '--alv-spice-soft': 'the spice accent'}

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
BASETXT = read(BASE)


def token(name):
    m = re.search(re.escape(name) + r'\s*:\s*(#[0-9a-fA-F]{3,6})\s*;',
                  BASETXT)
    return m.group(1) if m else None


def _rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lab(c):
    r, g, b = [v / 255.0 for v in (_rgb(c) if isinstance(c, str) else c)]

    def f(x):
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    X = r * 0.4124 + g * 0.3576 + b * 0.1805
    Y = r * 0.2126 + g * 0.7152 + b * 0.0722
    Z = r * 0.0193 + g * 0.1192 + b * 0.9505

    def g2(t):
        return t ** (1 / 3.0) if t > 0.008856 else 7.787 * t + 16 / 116.0
    fx, fy, fz = g2(X / 0.95047), g2(Y / 1.0), g2(Z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def dE(a, b):
    """CIE76. Crude next to dE2000 and ample for 'are these the same'."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(_lab(a), _lab(b))))


def rule(code, sel):
    m = re.search(re.escape(sel) + r'\s*\{([^}]*)\}', code)
    return m.group(1) if m else None


def bg(body):
    if not body:
        return None
    m = re.search(r'background(?:-color)?\s*:\s*([^;]+);', body)
    return m.group(1).strip() if m else None


def claims(bundle):
    code = T.code_only(bundle[TPL])
    row = rule(code, '.month-cell.in-week')
    c = {}
    c['THE BAND HAS A FILL - the finding'] = (
        bg(row) == 'var(%s)' % NEW)
    c['  and it is not any fill already on that grid'] = (
        bg(row) is not None
        and bg(row) not in ['var(%s)' % k for _, k in ON_GRID])
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

code = T.code_only(NOW[TPL])
row = rule(code, '.month-cell.in-week')

# GUARDS. True before this round and true after it - a claims() dict
# is a DELTA, and a guard put in it fails the control for being
# correct. Sixth time this shape has come up today.
ok('box-shadow' in (row or '') and 'var(--alv-accent)' in (row or ''),
   'the accent rule STAYS - two signals, not one. The fill says which '
   'week, the rule says it is a selection')
ok(bg(rule(code, '.month-chip')) == 'var(--alv-accent-soft)',
   'the PILL was not touched - three views share that token and only '
   'Month had the collision', bg(rule(code, '.month-chip')))
for sel, want in (('.month-cell', 'var(--alv-paper)'),
                  ('.month-cell.is-out', 'var(--alv-surface)')):
    ok(bg(rule(code, sel)) == want,
       'the other cell states are untouched: %s is still %s'
       % (sel, want), bg(rule(code, sel)))
ok(not re.search(r'#[0-9a-fA-F]{3,8}\b', row or ''),
   'and the band carries no literal colour', row)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
oldcode = T.code_only(BEFORE[TPL])
orow = rule(oldcode, '.month-cell.in-week')
ok(bg(orow) == 'var(--alv-paper)',
   'CONTROL: before this round the band had NO fill - it was paper, '
   'and the edge was doing all of the work', bg(orow))
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: and not one of this round claims held',
   'what held: %r' % (held,))
ok('there is no room for one' in BEFORE[TPL],
   'CONTROL: and the page said in so many words that there was no '
   'room for a fourth fill')
ok('there is no room for one' not in NOW[TPL],
   'which this round had to correct, not quietly drop')


# ==========================================================================
head('3. THE NUMBERS - THIRTEEN CANDIDATES, NOT TWO')
# ==========================================================================
# WT-1 measured two, found both too close, and concluded there was no
# room. The conclusion was the fault, not the arithmetic. Every pale
# tint base declares is asked here, against every fill already on the
# grid, worst case - so the next round proposing a sixth inherits a
# table rather than a sentence.
grid = [(n, token(k)) for n, k in ON_GRID]
if not all(h for _, h in grid) or not token(NEW):
    skip('the measurements', 'a token is missing from base')
else:
    print('')
    print('  already painted on the month grid:')
    for n, h in grid:
        print('     %-14s %s' % (n, h))
    print('')
    print('  %-22s %-9s %s' % ('candidate', 'hex', '  '.join(
        '%-6s' % n[:6] for n, _ in grid) + '   WORST'))
    rows = []
    for k in CANDIDATES:
        h = token(k)
        if not h:
            continue
        ds = [dE(h, g) for _, g in grid]
        rows.append((min(ds), k, h, ds))
    for worst, k, h, ds in sorted(rows, reverse=True):
        print('  %-22s %-9s %s   %5.1f%s'
              % (k.replace('--alv-', ''), h,
                 '  '.join('%6.1f' % d for d in ds), worst,
                 '  <- ' + MEANS[k] if k in MEANS else ''))
    print('')
    best = dict((k, w) for w, k, _, _ in rows)
    mine = best.get(NEW, 0.0)
    ok(mine >= VISIBLE * 3,
       'THE FILL THIS ROUND USES CLEARS EVERYTHING BY %.1f dE - three '
       'times the threshold a trained eye can just detect' % mine)
    # AND IT IS THE BEST ONE THAT MEANS NOTHING. bad-soft scores
    # higher and is the colour this application paints OVERDUE with;
    # a week band is not a status.
    neutral = [(w, k) for w, k, _, _ in rows if k not in MEANS]
    ok(neutral and max(neutral)[1] == NEW,
       '  and it is the best of the tints that carry no meaning - a '
       'band is not a status', sorted(neutral, reverse=True)[:3])
    ok(any(k in MEANS for w, k, _, _ in rows if w > mine),
       '  something scores higher, and it is a status colour, which '
       'is why it was not taken',
       [k for w, k, _, _ in rows if w > mine])
    # THE HALF OF WT-1 THAT WAS RIGHT.
    deep, surf, soft = token('--alv-surface-deep'), token(
        '--alv-surface'), token('--alv-accent-soft')
    ok(dE(surf, deep) < 5.0,
       'and the two WT-1 DID measure still fail: surface-deep is %.1f '
       'from is-out' % dE(surf, deep))
    ok(dE(surf, '#f0f8fa') < 3.0,
       '  and a pale accent closes on surface before it clears the '
       'pill: %.1f' % dE(surf, '#f0f8fa'))


# ==========================================================================
head('4. RENDERED, AND SAMPLED OFF THE SCREEN')
# ==========================================================================
# A TOKEN THAT RESOLVES IS NOT A PIXEL THAT PAINTS. Everything above
# reads a stylesheet; this reads the screen. CL-1 cost a day on
# exactly that gap - the rule's text was present and a later
# stylesheet won - so the band, and a meal, a note and a leftover
# sitting on it, are sampled out of the rendered pixels.
shot = {}
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
    import datetime as dt
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Recipe
    u = User.objects.create_user(username='wf1', password='x',
                                 email='wf1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Gemista', servings=6,
                              prep_time=10, cook_time=30)
    # ALL THREE PILL KINDS, INSIDE THE BAND. A band that only ever
    # carries meals proves nothing about the other two.
    p = MealEntry.objects.create(date=dt.date(2026, 10, 20), recipe=r,
                                 servings=6, created_by=u)
    MealEntry.objects.create(date=dt.date(2026, 10, 21), recipe=r,
                             servings=2, created_by=u, leftover_of=p)
    MealEntry.objects.create(date=dt.date(2026, 10, 22),
                             note='Dinner at Mums', created_by=u)
    cl = Client()
    cl.force_login(u)
    # FETCHED BEFORE A BROWSER IS OPENED. Playwright's sync API runs
    # its own event loop and the ORM called from inside it raises
    # SynchronousOnlyOperation, which looks like a database fault.
    page = cl.get('/meal_plans/',
                  {'view': 'month', 'date': '2026-10-21'}
                  ).content.decode('utf-8')
except Exception as ex:
    page = None
    skip('the rendered band',
         'Django would not start: %s' % str(ex).split('\n')[0][:90])

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if not page or sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the sampled pixels', 'playwright, the fixture or the page is '
                               'absent')
else:
    css = read(FIXCSS)

    def serve(r):
        u2 = r.request.url
        if 'bootstrap' in u2 and u2.endswith('.css'):
            return r.fulfill(status=200, body=css.encode('utf-8'),
                             content_type='text/css')
        return r.fulfill(status=200, body=b'', content_type='text/plain')

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        try:
            pg = br.new_page(viewport={'width': 1280, 'height': 1100})
            pg.route('**/*', serve)
            pg.set_content(
                re.sub(r'<head([^>]*)>',
                       r'<head\1><base href="http://127.0.0.1/">',
                       page, count=1),
                wait_until='domcontentloaded')
            pg.wait_for_timeout(350)
            shot = pg.evaluate("""() => {
                const rgb = (e, prop) => {
                    const v = getComputedStyle(e)[prop||'backgroundColor'];
                    const m = v.match(/(\\d+),\\s*(\\d+),\\s*(\\d+)/);
                    return m ? [+m[1], +m[2], +m[3]] : null;
                };
                const band = document.querySelector('.month-cell.in-week');
                if (!band) { return {err: 'no band'}; }
                const pick = (sel) => {
                    const e = document.querySelector(
                        '.month-cell.in-week ' + sel);
                    return e ? rgb(e) : null;
                };
                return {
                    band: rgb(band),
                    plain: pick('.month-chip:not(.is-note):not(.is-leftover)'),
                    note: pick('.month-chip.is-note'),
                    left: pick('.month-chip.is-leftover'),
                    rule: getComputedStyle(band).boxShadow,
                    cells: document.querySelectorAll(
                        '.month-cell.in-week').length,
                };
            }""")
            pg.close()
        finally:
            br.close()

if not shot or shot.get('err'):
    skip('the sampled pixels', shot.get('err', 'nothing was rendered'))
else:
    print('')
    print('  sampled out of the rendered page:')
    for k in ('band', 'plain', 'note', 'left'):
        print('     %-7s %s' % (k, shot.get(k)))
    print('     cells in the band: %s' % shot.get('cells'))
    print('')
    ok(shot.get('cells') == 7,
       'the band really is seven cells wide', shot.get('cells'))
    want = token(NEW)
    ok(shot.get('band') and dE(shot['band'], want) < 1.0,
       'THE BAND PAINTS THE TOKEN - not a later stylesheet winning, '
       'which is what CL-1 cost a day on',
       (shot.get('band'), want))
    ok('rgb' in (shot.get('rule') or ''),
       '  and the accent rule is painted too', shot.get('rule', '')[:70])
    for k, lab in (('plain', 'a meal'), ('note', 'a note'),
                   ('left', 'a leftover')):
        px = shot.get(k)
        if not px:
            ok(False, '  %s is on the band to be measured' % lab)
            continue
        d = dE(px, shot['band'])
        ok(d >= VISIBLE * 2,
           '  %-11s reads %.1f dE off the band it sits on' % (lab, d), d)


# ==========================================================================
head('5. WT-1 OWN SUITE, RUN')
# ==========================================================================
# This round corrects two of its claims in the same patcher. A claim
# moved is a claim that has to still fit.
# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN test_week_band IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims it was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(BAND) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(BAND))
ok('AND THE ONE WF-1 FOUND' in read(os.path.join(ROOT, BAND)),
   '  and it records that a fourth fill was found')


# ==========================================================================
head('6. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
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
ok(os.path.isfile(os.path.join(ROOT, BAND) + SUFFIX),
   'and so is WT-1 own suite, which this round corrects')
ok(MARK in read(os.path.join(ROOT, BAND)),
   '  which carries this round reason for the correction')
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_week_fill as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
