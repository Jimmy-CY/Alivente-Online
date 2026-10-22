# -*- coding: utf-8 -*-
"""test_print_range.py - round RG-2, 21 Oct 2026.

TWO OF THE ELEVEN, AND THEY BELONG TO ONE PAGE.

    "Why do we need to Press 'Print' twice. It is very inefficient."
    "Print Date Range needs to be included (similar to the Shopping
     List)"

THE PRINT PAGE HAS READ ?from= AND ?to= SINCE PP-1 BUILT IT. What it
could not do was let you type them. The only route to a different
fortnight was back to the planner, onto another view, and Print
again - which is also most of why pressing Print felt like two
presses for nothing.

AND THE SECOND PRESS CANNOT GO. window.print() IS the browser's own
dialog; there is no third thing this page could do instead, and a
page that printed itself on load would be a page you could not change
the dates on. He was offered three answers and chose: "Keep two
steps, make the second obvious." So what was missing was not a step.
It was a sentence.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. A GET form carrying the two dates the view reads,
      a secondary rather than a second primary, a line that says what
      the second press does - and neither of them on the paper.

  2   THE CONTROL. Re-asked of .bak_printrange, where the page had
      no form on it at all.

  3   DRIVEN. The row really re-asks the page: two dates in, a
      different sheet out, and the fields come back holding what was
      typed. A form that cannot round-trip its own values is a form
      that loses your dates on every refresh.

  4   MEASURED, at 1280 and at 390 - one line and two, 44px targets,
      nothing hanging off the side of a phone. SH-2 settled that
      shape on the shopping list this morning and this is the same
      row on the other page that takes the same two dates.

  5   AND NOT ON THE PAPER. In print media the row and the line
      measure zero, because a form on a fridge is a form nobody can
      fill in.

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
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_printrange'
ME = 'test_print_range.py'
PATCHER = 'apply_print_range.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'RG-2, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_print.html')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
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
BAR = re.compile(r'<(?:div|form)\b[^>]*class="[^"]*'
                 r'\bpage-action-buttons\b[^"]*"[^>]*>')


def form_of(code):
    """The range form's markup, or '' if the page has no form."""
    i = code.find('<form')
    if i < 0:
        return ''
    j = code.find('</form>', i)
    return code[i:j + 7] if j > i else ''


def claims(bundle):
    code = T.code_only(bundle[TPL])
    style = code[code.find('<style>'):code.find('</style>')]
    form = form_of(code)
    hint = ''
    m = re.search(r'<p[^>]*class="[^"]*\bpp-hint\b[^"]*"[^>]*>(.*?)</p>',
                  code, re.S)
    if m:
        hint = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1)))
    c = {}
    c['THE PAGE TAKES A RANGE OF ITS OWN - the finding'] = bool(form)
    c['  From and To, which is what the view reads'] = (
        sorted(re.findall(r'<input[^>]*name="(\w+)"', form))
        == ['from', 'to'])
    c['  as date fields, not typed text'] = (
        form.count('type="date"') == 2)
    c['  holding the range the page is already showing'] = (
        "value=\"{{ start|date:'Y-m-d' }}\"" in form
        and "value=\"{{ end|date:'Y-m-d' }}\"" in form)
    c['  a GET, so a refresh and a bookmark both survive'] = (
        'method="get"' in form[:90])
    c['  and a SECONDARY, because Print is the page verb'] = (
        'action-secondary' in form and 'action-primary' not in form)
    c['THE SECOND PRESS IS EXPLAINED'] = bool(hint)
    c['  it names the step and the button'] = (
        'Step 2 of 2' in hint and 'Print' in hint)
    c['  and says what comes back - the printer dialog'] = (
        'printer dialog' in hint)
    c['NEITHER OF THEM GOES ON THE PAPER'] = (
        'pp-range pp-noprint' in code and 'pp-hint pp-noprint' in code)
    c['  and the row is 44px, like every other field in the system'] = (
        '.pp-range-date' in style and 'height: 44px' in style)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

code = T.code_only(NOW[TPL])
style = code[code.find('<style>'):code.find('</style>')]
form = form_of(code)

# GUARDS. True before this round and true after it. A claims() dict is
# a DELTA; a guard put in it fails the control for being correct.
bars = BAR.findall(code)
ok(len(bars) == 1,
   'ONE action bar on the page - SL-7 wrote the shopping list range '
   'as <form class="sl-range page-action-buttons"> and gave that '
   'page two, which nothing could see until BA-1 this morning',
   len(bars))
roles = re.findall(r'class="btn (action-[a-z]+)"', code)
ok(roles.count('action-primary') == 1,
   'and exactly one primary on it - base 3.4', roles)
# SLICED FROM THE MARKUP, not the file. The print block names
# .page-action-buttons to hide it, and that mention is above
# everything in the body - a check that indexes the whole file
# measures a region running backwards and passes on an empty string.
mk = code[code.index('</style>'):]
before_bar = mk[mk.index('<div class="pp-page'):
                mk.index('page-action-buttons')]
ok(not re.search(r'<(?:form|input|button|table)\b', before_bar),
   'no CONTROL sits above the bar - base 3.4, "the bar is the first '
   'thing in the form"', before_bar[-120:])
ok('page-title-h2' in before_bar,
   'and the page TITLE does, which is the other rule - test_bar_top '
   'reads all 151 templates for it')
ok(mk.index('class="pp-sheet"') > mk.index('page-action-buttons'),
   'and the sheet itself is below everything that is not on paper')
naked = [m.group(1).strip()
         for m in re.finditer(r'@media([^{]*)\{', NOW[TPL])
         if 'max-width' in m.group(1) and 'screen' not in m.group(1)]
ok(not naked,
   'every width query still names screen - a bare one prints the '
   'phone layout', naked)
ok(not re.findall(r'#[0-9a-fA-F]{3,8}\b', style),
   'and not one literal colour arrived with the row',
   re.findall(r'#[0-9a-fA-F]{3,8}\b', style)[:6])


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: before this round not one of these held',
   'what held: %r' % (held,))
oldcode = T.code_only(BEFORE[TPL])
ok('<form' not in oldcode,
   'CONTROL: the page carried no form at all - the dates could only '
   'arrive in the URL, from the planner')
ok('pp-hint' not in oldcode,
   'CONTROL: and nothing on it said what the second Print press was '
   'for')


# ==========================================================================
head('3. DRIVEN - THE ROW REALLY RE-ASKS THE PAGE')
# ==========================================================================
got = {}
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
    u = User.objects.create_user(username='rg2', password='x',
                                 email='rg2@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Amygdalopita', servings=6,
                              prep_time=10, cook_time=20)
    for d in (19, 21, 26):
        MealEntry.objects.create(date=dt.date(2026, 10, d), recipe=r,
                                 servings=6, created_by=u)
    cl = Client()
    cl.force_login(u)
    for name, qs in (('month', {'from': '2026-10-01', 'to': '2026-10-31'}),
                     ('week', {'from': '2026-10-19', 'to': '2026-10-25'}),
                     ('day', {'from': '2026-10-21', 'to': '2026-10-21'}),
                     ('range', {'from': '2026-10-21',
                                'to': '2026-11-03'})):
        h = cl.get('/meal_plans/print/', qs).content.decode('utf-8')
        got[name] = {
            'html': h,
            'sheet': (re.findall(r'class="pp-page is-(\w+)"', h)
                      or ['?'])[0],
            'from': (re.findall(r'id="ppFrom"[^>]*value="([^"]*)"', h)
                     or re.findall(r'value="([^"]*)"[^>]*id="ppFrom"', h)
                     or [''])[0],
            'to': (re.findall(r'id="ppTo"[^>]*value="([^"]*)"', h)
                   or re.findall(r'value="([^"]*)"[^>]*id="ppTo"', h)
                   or [''])[0],
            'hint': re.sub(r'\s+', ' ', re.sub(
                r'<[^>]+>', ' ', (re.findall(
                    r'<p class="pp-hint pp-noprint">(.*?)</p>', h, re.S)
                    or [''])[0])).strip(),
        }
except Exception as ex:
    skip('the driven checks',
         'Django would not start: %s' % str(ex).split('\n')[0][:90])

if not got:
    skip('the round trip', 'nothing was asked')
else:
    print('')
    for k in ('month', 'week', 'day', 'range'):
        print('  %-6s sheet=%-6s fields=%s..%s'
              % (k, got[k]['sheet'], got[k]['from'], got[k]['to']))
    print('')
    print('  the line on the day sheet:')
    print('      %s' % got['day']['hint'][:120])
    print('')
    ok(got['month']['from'] == '2026-10-01'
       and got['month']['to'] == '2026-10-31',
       'THE FIELDS COME BACK HOLDING THE RANGE ASKED FOR - a form '
       'that cannot round-trip its own values loses your dates on '
       'every refresh', (got['month']['from'], got['month']['to']))
    ok(got['week']['from'] == '2026-10-19'
       and got['week']['to'] == '2026-10-25',
       '  for a different range too', (got['week']['from'],
                                       got['week']['to']))
    ok(len(set(g['sheet'] for g in got.values())) == 4,
       'AND TYPING TWO DATES CHANGES THE SHEET - which is the whole '
       'point of being able to type them',
       dict((k, v['sheet']) for k, v in got.items()))
    # THE LINE TELLS THE TRUTH ABOUT THE PAPER. RG-1 puts a day on
    # portrait and everything else on landscape; a sentence that said
    # otherwise would be worse than no sentence.
    ok('portrait' in got['day']['hint'],
       'the line says portrait on the day sheet', got['day']['hint'][:90])
    ok('landscape' in got['month']['hint']
       and 'landscape' in got['week']['hint'],
       '  and landscape on the week and the month')
    ok('one A4 sheet' not in got['range']['hint'],
       '  and claims nothing about a range, which is as long as it is',
       got['range']['hint'][:90])
    for k in ('day', 'week', 'month', 'range'):
        ok('Step 2 of 2' in got[k]['hint'],
           '  %-6s names the step' % k, got[k]['hint'][:70])


# ==========================================================================
head('4. MEASURED, AT 1280 AND AT 390')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

seen = {}
if sync_playwright is None or not os.path.isfile(FIXCSS) or not got:
    skip('the measured row', 'playwright, the fixture or the page is '
                             'absent')
else:
    css = read(FIXCSS)

    def serve(r):
        u = r.request.url
        if 'bootstrap' in u and u.endswith('.css'):
            return r.fulfill(status=200, body=css.encode('utf-8'),
                             content_type='text/css')
        return r.fulfill(status=200, body=b'', content_type='text/plain')

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        try:
            for w, where in ((1280, 'desktop'), (390, 'phone')):
                pg = br.new_page(viewport={'width': w, 'height': 1000})
                pg.route(re.compile(r'^https?://'), serve)
                pg.set_content(got['month']['html'],
                               wait_until='domcontentloaded')
                pg.wait_for_timeout(120)
                row = pg.evaluate("""() => [...document.querySelectorAll(
                        '.pp-range > *')].map(e => {
                    const r = e.getBoundingClientRect();
                    return {t: Math.round(r.top), h: Math.round(r.height),
                            l: Math.round(r.left),
                            r: Math.round(r.right)};
                })""")
                doc = pg.evaluate(
                    "() => {const s = document.scrollingElement;"
                    " return [s.scrollWidth, s.clientWidth];}")
                # AND THE SAME PAGE ON PAPER.
                pg.emulate_media(media='print')
                pg.wait_for_timeout(60)
                paper = pg.evaluate("""() => {
                    const h = (s) => {const e =
                        document.querySelector(s);
                        return e ? Math.round(
                            e.getBoundingClientRect().height) : -1;};
                    return {range: h('.pp-range'), hint: h('.pp-hint'),
                            bar: h('.page-action-buttons'),
                            sheet: h('.pp-sheet')};
                }""")
                pg.close()
                seen[where] = {'row': row, 'doc': doc, 'paper': paper}
        finally:
            br.close()

if not seen:
    skip('the two widths', 'nothing was measured')
else:
    for where in ('desktop', 'phone'):
        s = seen[where]
        lines = sorted(set(x['t'] for x in s['row']))
        print('')
        print('  --- %s ---' % where)
        for x in s['row']:
            print('     top %-4d height %-3d  %d..%d'
                  % (x['t'], x['h'], x['l'], x['r']))
        print('     lines %d, page %s, on paper %s'
              % (len(lines), s['doc'], s['paper']))
        ok(len(s['row']) == 3,
           '%-7s the row is two fields and one button' % where,
           len(s['row']))
        ok(all(x['h'] >= 44 for x in s['row']),
           '  every control is a 44px target, which 3.4 promises',
           [x['h'] for x in s['row']])
        if where == 'desktop':
            ok(len(lines) == 1,
               '  and all three sit on ONE line - he asked for that on '
               'the shopping list this morning and it is the same row',
               lines)
        else:
            ok(len(lines) == 2,
               '  two lines on a phone, not three: the two dates share '
               'the first and the button takes the second', lines)
            ok(s['doc'][0] <= s['doc'][1] + 1,
               '  with nothing hanging off the side of a 390px screen',
               s['doc'])
            ok(all(x['r'] <= 390 for x in s['row']),
               '  and no control reaching past the edge',
               [x['r'] for x in s['row']])


# ==========================================================================
head('5. AND NOT ON THE PAPER')
# ==========================================================================
if not seen:
    skip('the print media', 'nothing was measured')
else:
    p = seen['desktop']['paper']
    print('')
    print('  heights in print media: %s' % p)
    print('')
    ok(p['range'] == 0 and p['hint'] == 0,
       'THE ROW AND THE LINE MEASURE ZERO ON PAPER - a form on a '
       'fridge is a form nobody can fill in', p)
    ok(p['bar'] == 0, '  and so does the bar, as SL-1 does it', p)
    ok(p['sheet'] > 400,
       '  while the sheet itself is still there, which is the check '
       'that keeps the one above honest', p)


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

# THE ONE CENSUS THIS ROUND MOVED.
pc = os.path.join(ROOT, 'test_pair_contrast.py')
ok(MARK in read(pc),
   'test_pair_contrast carries this round reason for its new number')
# MN-2, 21 Oct 2026 - THE TOTAL MOVED AGAIN, and this claim is about
# what RG-2 DID, not about what the tree holds today. RG-2 added two
# pairs and took the census from 724 to 726; MN-2 adds the Saved Menus
# preset row and takes it to 727. Asking for today's total here would
# make a 21 October round's record change every time somebody adds a
# rule, which is the opposite of a record.
ok("# RG-2, 21 Oct 2026" in read(pc)
   and "(was 724)" in read(pc),
   '  and RG-2 two pairs are still in its history, 724 -> 726')
ok(os.path.isfile(pc + SUFFIX), '  and it is backed up')

patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_print_range as PATCH                           # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
