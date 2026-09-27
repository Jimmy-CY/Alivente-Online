# -*- coding: utf-8 -*-
"""test_bar_mobile.py - Section H round H2b, 27 Sep 2026.

Judges three phone faults found straight after H2 deployed. They have three
different causes and only two of them are H2's.

EVERY CLAIM HERE IS RENDERED AT 390px. "The bar fits" and "Back is on the
right" are claims about geometry; no amount of reading a stylesheet settles
either, and the first form of this round's base fix was believed for about a
minute on the strength of the CSS alone.

ONE BRANCH, NOT TWO. Four of these bars hold an {% if %}/{% else %} pair -
a permitted control and its no-permission twin, or two destinations - and
the fixture strips template tags, so BOTH render and the bar looks twice as
crowded as it is. Section 2 removes the duplicates as Django would before
measuring. Without that, three correct pages read as failures.
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

import os
import re
import sys

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_barmobile'
ME = 'test_bar_mobile.py'
PATCHER = 'apply_bar_mobile.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

DASH = os.path.join(T, 'celebration_dashboard.html')
MGMT = os.path.join(T, 'celebration_management.html')
CAL = os.path.join(T, 'celebration_calendar.html')

RULE = '.page-action-buttons:not(:has(.action-primary)) .action-back'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)

# Measured BEFORE the round, at 390px: how far Back sat from the right edge.
WAS_ADRIFT = {
    'celebration_calendar.html': 316,
    'unit_conversions_wizard.html': 300,
    'finance.html': 236,
    'notification_settings.html': 236,
    'occupancy_trends.html': 220,
    'passport_management.html': 184,
}
# It was never wrong here - this page HAS a primary taking the slack.
CONTROL_OK = 'properties.html'

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
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def css_of(t):
    """Style bodies with CSS COMMENTS STRIPPED. Both of this round's own
    self-checks first counted a brace and a class name that appeared only
    inside the note explaining them - a comment is not code, in this
    direction too (lesson 21)."""
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)), flags=re.S)


def markup_no_comments(t):
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


# ==========================================================================
head('1. base: A BAR WITH NO PRIMARY KEEPS BACK ON THE RIGHT')
# ==========================================================================
bc = css_of(read(BASE))
ok(bc.count(RULE) == 1, 'base declares the rule exactly once',
   bc.count(RULE))
m = re.search(re.escape(RULE) + r'\s*\{([^}]*)\}', bc)
ok(m is not None and 'margin-left: auto' in m.group(1),
   '  and it restores margin-left: auto', m.group(1).strip() if m else '')
# it belongs INSIDE the phone block, beside the rule it corrects
i = bc.find(RULE)
j = bc.find('.page-action-buttons .action-back {\n          margin-left: 0;')
ok(j >= 0 and i > j,
   '  placed after the `margin-left: 0` it qualifies, in the same block',
   'rule at %d, margin-left:0 at %d' % (i, j))
a, b = was(BASE), now(BASE)
ok(re.sub(r'<style[^>]*>.*?</style\s*>', '', a, flags=re.S | re.I)
   == re.sub(r'<style[^>]*>.*?</style\s*>', '', b, flags=re.S | re.I),
   '  and nothing outside the stylesheet moved')
ok(css_of(a).count('{') + 1 == css_of(b).count('{'),
   '  exactly ONE rule was added',
   '%d -> %d' % (css_of(a).count('{'), css_of(b).count('{')))

# ==========================================================================
head('2. RENDERED AT 390px - BACK IS AT THE RIGHT EDGE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    sync_playwright = None
    skip('sections 2 and 3', 'playwright unavailable: %s' % str(e)[:40])

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 2 and 3', 'playwright or the bootstrap fixture is missing')
else:
    MODAL_IF = re.compile(
        r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)

    def styles_of(t):
        return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', mm.group(1)),
                       flags=re.S)
                for mm in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                      re.S | re.I)]

    def body_markup(t):
        mm = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t,
                       re.S)
        x = mm.group(1) if mm else t
        x = re.sub(r'<(script|style)\b.*?</\1>', '', x, flags=re.S | re.I)
        for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
            x = re.sub(rx, '', x, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', x, flags=re.S)

    boot = read(BOOT)

    def fixture(t, base_text):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s</head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, '\n'.join(styles_of(base_text)),
                   ''.join('<style>%s</style>' % c for c in styles_of(t)),
                   body_markup(t)))

    # ONE BRANCH, AS DJANGO RENDERS. The fixture strips {% if %}, so a
    # permitted control and its no-permission twin BOTH appear.
    GEOM = """() => {
        const b = document.querySelector('.page-action-buttons');
        if (!b) return null;
        [...b.querySelectorAll('.action-back')].slice(1).forEach(e=>e.remove());
        [...b.querySelectorAll('.action-add-new')].slice(1).forEach(e=>e.remove());
        [...b.querySelectorAll('.action-primary')].slice(1).forEach(e=>e.remove());
        const back = b.querySelector('.action-back');
        const r = b.getBoundingClientRect();
        const vis = [...b.children].filter(
            e => getComputedStyle(e).display !== 'none');
        return {
            gap: back ? Math.round(r.right - back.getBoundingClientRect().right)
                      : null,
            clipped: vis.filter(e => e.scrollWidth > e.clientWidth + 1).length,
            visible: vis.length
        };
    }"""

    launched = False
    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            launched = True
        except Exception as _e:
            skip('sections 2 and 3', 'chromium would not launch: %s'
                 % str(_e).split('\n')[0][:60])

        if launched:
            n = [0]

            def probe(text, base_text, js, w=390):
                n[0] += 1
                fx = os.path.join(SCRATCH, 'bm_%04d.html' % n[0])
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text, base_text))
                ctx = br.new_context(viewport={'width': w, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, fx)
                try:
                    return pg.evaluate(js)
                finally:
                    ctx.close()

            b_now, b_was = now(BASE), was(BASE)
            fixed = 0
            for rel, adrift in sorted(WAS_ADRIFT.items()):
                p = os.path.join(T, rel)
                if not os.path.isfile(p):
                    skip(rel, 'not on disk')
                    continue
                g = probe(now(p), b_now, GEOM)
                ok(g is not None and g['gap'] == 0,
                   '%-30s Back is at the right edge (was %dpx adrift)'
                   % (rel, adrift), g)
                # CONTROL: under the OLD base it was not.
                gw = probe(was(p), b_was, GEOM)
                ok(gw is not None and gw['gap'] > 4,
                   '  CONTROL: under the old base CSS it was %spx adrift - '
                   'the check can be seen failing'
                   % (gw['gap'] if gw else '?'), gw)
                fixed += 1
            ok(fixed >= 5, 'at least five pages measured', fixed)
            pc = os.path.join(T, CONTROL_OK)
            if os.path.isfile(pc):
                g = probe(now(pc), b_now, GEOM)
                gw = probe(was(pc), b_was, GEOM)
                ok(g and gw and g['gap'] == gw['gap'] == 0,
                   'CONTROL: %s was ALREADY correct and did not move - it '
                   'has a primary taking the slack' % CONTROL_OK,
                   '%s vs %s' % (gw, g))

            # ==============================================================
            head('3. THE DASHBOARD BAR FITS ON A PHONE')
            # ==============================================================
            if not os.path.isfile(DASH):
                skip('section 3', 'not on disk')
            else:
                g = probe(now(DASH), b_now, GEOM)
                gw = probe(was(DASH), b_was, GEOM)
                ok(gw is not None and gw['clipped'] >= 1,
                   'CONTROL: before this round the bar CLIPPED %s control(s)'
                   % (gw['clipped'] if gw else '?'), gw)
                ok(g is not None and g['clipped'] == 0,
                   'after: nothing is clipped', g)
                ok(g is not None and g['visible'] == 3,
                   '  and three controls show - primary, More, Back', g)
                ok(g is not None and g['gap'] == 0,
                   '  with Back at the right edge', g)
                b = markup_no_comments(now(DASH))
                ok(b.count('action-more-btn') == 1,
                   '  exactly one More button', b.count('action-more-btn'))
                ok(b.count('View Events') == 2 and b.count('Help') >= 2,
                   '  each secondary is named twice - in the bar and in the '
                   'menu, which is how base hides one and shows the other')
            br.close()

# ==========================================================================
head('4. THE SEARCH IS WHERE THE HOUSE PUTS IT')
# ==========================================================================
if not os.path.isfile(MGMT):
    skip('section 4', 'not on disk')
else:
    a, b = was(MGMT), now(MGMT)
    ok('toolbar-search' in a,
       'before: the search sat above the bar in its own .toolbar-search')
    ok('toolbar-search' not in markup_no_comments(b),
       'after: that wrapper is gone from the markup')
    ok('id="celebrationFilterPanel"' in b,
       '  and the field lives in a .alv-filter panel')
    mm = re.search(r'<div[^>]*class="([^"]*)"[^>]*id="celebrationFilterPanel"',
                   b)
    ok(mm is not None and 'alv-filter' in mm.group(1).split(),
       '  which wears base\'s own .alv-filter', mm.group(1) if mm else '')
    btn = re.search(r'<button[^>]*class="([^"]*action-filter[^"]*)"[^>]*'
                    r'aria-controls="([^"]*)"', b, re.S)
    ok(btn is not None and btn.group(2) == 'celebrationFilterPanel',
       '  opened by a .action-filter whose aria-controls names it - which '
       'is how base pairs the two',
       btn.group(2) if btn else 'no .action-filter with aria-controls')
    ok(b.count('id="contactSearch"') == 1
       and 'onkeyup="searchContacts()"' in b,
       '  the field and its handler are unchanged',
       b.count('id="contactSearch"'))
    ok('search-input' in b,
       '  and it wears .search-input, as properties.html does')
    # THE HOUSE SHAPE, READ OFF THE HOUSE.
    props = os.path.join(T, 'properties.html')
    if os.path.isfile(props):
        pt = read(props)
        ok('search-input' in pt and 'alv-filter' in pt,
           'CONTROL: properties.html - the page this was matched against - '
           'keeps its search in a .alv-filter panel too')
    ok('style="width: 250px;"' not in b,
       '  and the 250px inline width is gone')

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
ok(css_of('<style>/* .foo { x } */ .bar { y }</style>').count('{') == 1,
   'the CSS reader ignores a brace inside a comment - this round\'s own '
   'self-check counted one and refused a correct edit')
ok('action-more-btn' not in markup_no_comments(
    '<!-- names .action-more-btn --><div></div>'),
   '  and the markup reader ignores a class named only in a comment - the '
   'same fault, twice in one round')
ok(re.search(r':has\(', css_of(read(BASE))) is not None,
   ':has() is already house vocabulary in base - this invents no technique')
cal = CAL
if os.path.isfile(cal):
    ok('action-primary' not in read(cal),
       'CONTROL: celebration_calendar really has no primary, which is why '
       'its Back had nothing to push it right')
if os.path.isfile(BASE + SUFFIX):
    ok(RULE not in css_of(was(BASE)),
       'reverting base removes the rule, so section 2 would FAIL - a '
       'revert is caught')
else:
    skip('the revert check', 'no %s backup' % SUFFIX)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ok(SUFFIX in ROUNDS and '.bak_bodybacks' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_bodybacks'),
   '  and after the round before it (lesson 54)')
ps1 = os.path.join(ROOT, PS1)
ok(os.path.isfile(ps1) and ME in read(ps1), '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
