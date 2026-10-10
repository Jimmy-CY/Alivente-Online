# -*- coding: utf-8 -*-
"""test_form_grid.py - Section D round D-4, 10 Oct 2026.

TWELVE PAGES WROTE THE SAME COMPONENT. BASE SAYS IT ONCE.

Eleven of them agreed character for character, down to an 18px/22px
gap. The twelfth spelled the columns repeat(2, 1fr) and used 14px, and
adopted the majority on his call, from a render.

THE CLAIM IS THAT ONE GRID MOVED AND TWENTY-THREE DID NOT, which is a
claim about rendered boxes. Section 5 renders all twelve pages twice -
once as this round left them, once from the backups - and compares the
computed columns, the gap, and the position and width of every child.
Exactly one difference is allowed, and it is named.

HERMETIC, AND IT COUNTS WHAT IT REFUSED. The sweep before this one
passed in a sandbox with no route to a CDN and then failed his push:
34 templates pull Font Awesome, base pulls Bootstrap, and on a machine
that can reach them the two renders raced. test_tap_target and
test_control_height had the right line all along. So section 5 blocks
the network AND asserts the browser refused something - a route I
added is not a measurement.

WHAT THIS ROUND IS NOT. It does not unblock IN-2, which the
outstanding list said it would: customer_invoice_form does not use
this class at all and its sideways scroll comes from a table with a
720px minimum width. It does not touch the rest of the form family -
44 pages, 111 rules, including a real disagreement about the card
radius on a phone and four pages setting a label weight against a
decision settled on 9 Sep. Those are named in the doc, not swept.

NOT PROVED HERE: that two columns at 18px/22px is the right field row.
Eleven pages had already decided that; this round only stops them each
saying it separately.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------


import collections
import json
import os
import re
import sys

ROOT = os.getcwd()
if not os.path.isdir(os.path.join(ROOT, 'pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_formgrid'
ME = 'test_form_grid.py'
PATCHER = 'apply_form_grid.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'

N_PAGES, N_DESK, N_PHONE, N_FULL = 12, 12, 12, 4
N_REMOVED = N_DESK + N_PHONE + N_FULL
N_MOVED = 1
MOVER = 'crs/submission_detail.html'
N_BARE_LEFT = 6       # CRS pages whose phone query still has no `screen`

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
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


print(__doc__.strip().splitlines()[0])

import alv_rounds as RD                                       # noqa: E402
import alv_tree as T                                          # noqa: E402

DESK = re.compile(r'\.form-grid\s*\{[^}]*display:\s*grid[^}]*\}')
PHONE = re.compile(r'\.form-grid\s*\{(?![^}]*display:\s*grid)[^}]*\}')
FULL = re.compile(r'\.form-group-full\s*\{[^}]*\}')
USES = re.compile(r'class="[^"]*\bform-grid\b')


def left_by(p):
    '''The file as THIS round left it, not as it is now.'''
    return RD.as_left_by(p, SUFFIX, read)


# ==========================================================================
head('1. SCOPE')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
BP = T.path_of('base.html')
base_now = left_by(BP)
applied = 'D-4, 10 Oct 2026' in base_now
ok(applied, 'base.html carries the round note')
if not applied:
    skip('every later section', 'D-4 is not applied to this tree.')
    print('')
    print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
    sys.exit(1 if failed else 0)


# ==========================================================================
head('2. BASE IS THE ONLY PLACE THE COMPONENT IS DECLARED')
# ==========================================================================
bc = T.code_only(base_now)
ok(len(DESK.findall(bc)) == 1, 'base declares .form-grid once',
   len(DESK.findall(bc)))
ok(len(PHONE.findall(bc)) == 1, '  and its phone collapse once',
   len(PHONE.findall(bc)))
ok(len(FULL.findall(bc)) == 1, '  and .form-group-full once',
   len(FULL.findall(bc)))
m = DESK.search(bc)
body = ' '.join(m.group(0).split()) if m else ''
ok('1fr 1fr' in body and '18px 22px' in body,
   '  with the two columns and the gap eleven pages already agreed on',
   body[:80])

strays = []
for p in sorted(T.templates()):
    if os.path.abspath(p) == os.path.abspath(BP):
        continue
    c = T.code_only_js(left_by(p))
    n = len(DESK.findall(c)) + len(PHONE.findall(c)) + len(FULL.findall(c))
    if n:
        strays.append('%s: %d' % (T.rel(p).replace(os.sep, '/'), n))
ok(not strays, 'and NO page declares either of them any more', strays[:8])

# CONTROL: a detector that finds nothing reads the same as a clean tree.
ok(len(DESK.findall('.form-grid { display: grid; }')) == 1,
   'CONTROL: the detector does find a planted rule')
ok(len(PHONE.findall('.form-grid { display: grid; }')) == 0,
   '  and the phone pattern refuses the desktop one, so the two counts '
   'above are not the same rule counted twice')


# ==========================================================================
head('3. WHAT CAME OUT, MEASURED AGAINST THE BACKUPS')
# ==========================================================================
pages = [p for p in sorted(T.templates()) if os.path.isfile(p + SUFFIX)
         and os.path.abspath(p) != os.path.abspath(BP)]
d = ph = f = 0
for p in pages:
    was = T.code_only_js(read(p + SUFFIX))
    d += len(DESK.findall(was))
    ph += len(PHONE.findall(was))
    f += len(FULL.findall(was))
ok(len(pages) == N_PAGES, '%d page(s) carried the component' % len(pages),
   'pinned at %d' % N_PAGES)
ok((d, ph, f) == (N_DESK, N_PHONE, N_FULL),
   '  and between them %d rule(s): %d desktop, %d phone, %d full-width'
   % (d + ph + f, d, ph, f),
   'pinned at %d, %d, %d' % (N_DESK, N_PHONE, N_FULL))


# ==========================================================================
head('4. EVERY PAGE THAT USES THE CLASS IS SERVED BY BASE')
# ==========================================================================
users = [T.rel(p).replace(os.sep, '/') for p in sorted(T.templates())
         if USES.search(left_by(p))]
ok(len(users) == N_PAGES, '%d page(s) use class form-grid' % len(users),
   'pinned at %d' % N_PAGES)
ok(sorted(users) == sorted(T.rel(p).replace(os.sep, '/') for p in pages),
   '  and they are exactly the %d that used to declare it - so the round '
   'took nothing away from a page it did not also give base' % N_PAGES,
   sorted(set(users) ^ {T.rel(p).replace(os.sep, '/') for p in pages}))


# ==========================================================================
head('5. MEASURED: ONE GRID MOVED, TWENTY-THREE DID NOT')
# ==========================================================================
up = False
try:
    from playwright.sync_api import sync_playwright
    import atexit
    if not os.path.isfile(os.path.join(ROOT, BOOT)):
        raise RuntimeError('%s is missing' % BOOT)
    _pw = sync_playwright().start()
    atexit.register(_pw.stop)
    _br = _pw.chromium.launch()
    up = True
except Exception as _e:
    skip('section 5', 'Chromium or the Bootstrap fixture is unavailable: %s'
         % str(_e).split('\n')[0][:66])

if up:
    boot = read(os.path.join(ROOT, BOOT))
    base_was = read(BP + SUFFIX) if os.path.isfile(BP + SUFFIX) else base_now

    def styles_of(t):
        return [re.sub(r'\{%.*?%\}', '', mm.group(1), flags=re.S)
                for mm in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                      re.S | re.I)]

    def body_markup(t):
        mm = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
        b = mm.group(1) if mm else t
        b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
        b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
        b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)

    def doc(base_src, t):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style></head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, '\n'.join(styles_of(base_src)),
                   ''.join('<style>%s</style>' % c for c in styles_of(t))
                   + body_markup(t)))

    JS = '''() => {
      const o = [];
      document.querySelectorAll('.form-grid').forEach(g => {
        const s = getComputedStyle(g);
        o.push([s.gridTemplateColumns, s.gap,
                [...g.children].map(c => {
                  const r = c.getBoundingClientRect();
                  return [Math.round(r.left), Math.round(r.width)];
                })]);
      });
      return o;
    }'''

    REFUSED = []
    probe = None
    moved, grids = [], 0
    for w in (1280, 390):
        ctx = _br.new_context(viewport={'width': w, 'height': 900})

        def _offline(route, request):
            REFUSED.append(request.url)
            route.abort()

        ctx.route(re.compile(r'^https?://'), _offline)
        pg = ctx.new_page()
        if probe is None:
            pg.set_content('<!doctype html><html><body>x</body></html>')
            probe = pg.evaluate(
                '''() => fetch('https://cdn.example.invalid/probe.css')
                       .then(() => 'loaded').catch(() => 'blocked')''')
        for p in pages:
            rel = T.rel(p).replace(os.sep, '/')
            pg.set_content(doc(base_now, left_by(p)))
            a = pg.evaluate(JS)
            pg.set_content(doc(base_was, read(p + SUFFIX)))
            b = pg.evaluate(JS)
            grids += len(a)
            if a != b:
                moved.append((rel, w, a, b))
        ctx.close()
    try:
        _br.close()
    except Exception:
        pass

    # A ROUTE I ADDED IS NOT A MEASUREMENT - and on THESE twelve pages
    # the honest refusal count is zero, because none of them carries a
    # remote link inside its content block. Asserting a count that
    # cannot happen is worse than not checking at all: it would read
    # green on a route that was never installed. So the route is PROVED
    # instead, by asking the page to fetch something and watching it be
    # refused. The sweep before this one passed in a sandbox with no
    # route out and then failed his push; this is that lesson with a
    # control on it.
    ok(probe == 'blocked' and len(REFUSED) > 0,
       'CONTROL: the page asked for a remote stylesheet and the browser '
       'REFUSED it (%d request(s) blocked) - so these renders cannot '
       'depend on what a CDN served today' % len(REFUSED),
       '%r, refused=%s' % (probe, REFUSED[:2]))
    ok(grids >= 24, 'measured %d grid render(s) across %d page(s) at two '
       'widths' % (grids, len(pages)), grids)
    ok(len(moved) == N_MOVED,
       'exactly %d grid(s) changed' % len(moved),
       '\n'.join('%s @%d' % (r, w) for r, w, _a, _b in moved[:6]))
    if len(moved) == N_MOVED:
        rel, w, a, b = moved[0]
        ok(rel == MOVER and w == 1280,
           '  and it is %s at 1280px - the one page that wrote a 14px gap '
           'where eleven wrote 18px/22px' % rel, '%s @%d' % (rel, w))
        ok(b[0][1] == '14px' and a[0][1] == '18px 22px',
           '  gap %s -> %s, which is the change he approved from a render'
           % (b[0][1], a[0][1]), (a[0][1], b[0][1]))
        ok(all(x[0] == y[0] for x, y in zip(a, b)) is False
           or a[0][0] != b[0][0],
           '  and the columns narrow to absorb it: %s -> %s'
           % (b[0][0], a[0][0]))


# ==========================================================================
head('6. THE PHONE RULE SAYS screen - AND SIX CRS PAGES STILL DO NOT')
# ==========================================================================
mq = re.search(r'@media([^{]*)\{[^{}]*\.form-grid', bc)
ok(mq is not None and 'screen' in mq.group(1),
   "base's phone rule carries the screen keyword, so it cannot fire on "
   'paper - A4 portrait is about 718 CSS px',
   mq.group(1).strip() if mq else '(not found)')

bare = []
for p in sorted(T.templates()):
    rel = T.rel(p).replace(os.sep, '/')
    if rel == 'base.html':
        continue
    c = T.code_only(left_by(p))
    for mm in re.finditer(r'@media\s*([^{]+)\{', c):
        q = ' '.join(mm.group(1).split())
        if 'screen' not in q and 'print' not in q and 'max-width' in q:
            bare.append(rel)
bare = sorted(set(bare))
ok(len(bare) == N_BARE_LEFT,
   'and %d CRS page(s) still carry a bare one, which this round did NOT '
   'fix' % len(bare), 'pinned at %d - %s' % (N_BARE_LEFT, bare))
print('')
print('       TWO OF THE EIGHT CLOSED AS A SIDE EFFECT, not as a fix:')
print('       their phone block held nothing but the grid rule, so taking')
print('       the rule emptied it. The remaining six print the phone')
print('       layout, and test_print_queries cannot see any of them - it')
print('       walks pages/templates and these live in crs/templates. That')
print('       is a round of its own, named here so the number cannot drop')
print('       quietly and look like progress.')


# ==========================================================================
head('7. THE STANDARDS BLOCK SAYS SO, IN THE SAME ROUND')
# ==========================================================================
ok('.form-grid' in base_now and 'D-4, 10 Oct' in base_now,
   'the block names the component and the round')
i = base_now.find('{% comment %}')
j = base_now.find('{% endcomment %}')
blk = base_now[i:j] if (i >= 0 and j > i) else ''
ok(blk and '{' not in blk.replace('{% comment %}', '')
   and '}' not in blk.replace('{% comment %}', ''),
   'and it contains no brace - prose shaped like a declaration once sent '
   'a suite seven thousand characters forward to the wrong token and cost '
   'a push',
   [s for s in blk.split('\n') if '{' in s or '}' in s][:3])


# ==========================================================================
head('8. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % SUFFIX in rounds
   and rounds.index("'%s'" % SUFFIX) > rounds.index("'.bak_radtoken'"),
   '  and after D-12, which is the ordering as_left_by needs')
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that two columns at 18px/22px is the right')
print('  field row. Eleven pages had already decided that; this round')
print('  only stops them each saying it separately - and gives the')
print('  twelfth a reason to differ, or none.')
sys.exit(1 if failed else 0)
