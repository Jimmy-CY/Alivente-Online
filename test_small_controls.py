# -*- coding: utf-8 -*-
"""test_small_controls.py - every text control is 16px on a phone, so iOS
does not zoom the page when one is tapped; and nothing else moved.

    python test_small_controls.py

Run from the repo root. Paired with apply_small_controls.py (21 Sep).

  1. base carries the rule - once, screen-only, below 768px, on inputs,
     selects and textareas, skipping the types iOS does not zoom on.
  2. dashboard_pl's year select lost one word: the !important on its
     inline font-size, which no stylesheet could outrank.
  3. THE INVARIANT, rendered: every page that extends base at 375 - no
     text control under 16px. And the other half: every control that
     moved at 375 was one that was small, and at 1280 nothing moved.
  4. CONTROLS, on a fixture of our own so they never expire: a page rule,
     an inline style and a number input, small on the desktop and 16px on
     a phone; the same with the rule taken back out of base must come out
     small, or section 3 could not see a failure; a checkbox is left
     alone; and an inline !important - the one thing base cannot reach -
     must be caught by the same scan section 3 uses.
  5. It is on the gate.
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
# This suite renders a fixture in Chromium, and a fixture has to be a real
# file before file:// can reach it. Those files used to be written into
# the repo root. Three things are wrong with that, and the third one bit:
#
#   - the root is a git working tree, so a suite that dies before its own
#     cleanup leaves an untracked file where the next commit can see it;
#   - the root is inside OneDrive, so every fixture is a create, an upload
#     and a delete for the sync client to chase;
#   - THE NAME WAS NOT UNIQUE. Four suites all wrote _sup_probe.html into
#     that one directory. On the push gate test_table_tenants.py runs
#     immediately before test_table_lease_agreement.py, so the same path
#     was created, deleted and created again within a second or two, and
#     Chromium answered the second one with net::ERR_FAILED. Run
#     alphabetically by Show-GateAudit.py the order is different, nobody
#     hands another suite a path they have just deleted, and the same
#     suite passes - which is why this read as a fault in the gate.
#
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however they are ordered, and
# nothing is written into the working tree at all.
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

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_smallctl'
BOOT = 'test_fixture_bootstrap413.css'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_small_controls.py'
MARK = re.compile(r'/\* ALV SMALL CONTROLS v1\b.*?/\* /ALV SMALL CONTROLS v1 \*/',
                  re.S)
COMMENT = re.compile(r'/\*.*?\*/', re.S)
SKIP_TYPES = ('checkbox', 'radio', 'hidden', 'submit', 'button', 'reset',
              'file', 'image', 'range', 'color')

passed = failed = skipped = 0
notes = []


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


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S)]


def body_markup(t):
    """The content block, Django stripped, scripts out. Every branch of every
    conditional is kept, which can only ADD controls."""
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                  t, re.S)
    body = m.group(1) if m else t
    body = re.sub(r'<(script|style)\b.*?</\1>', '', body, flags=re.S | re.I)
    body = re.sub(r'\{#.*?#\}', '', body, flags=re.S)
    body = re.sub(r'\{%.*?%\}', '', body, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', body, flags=re.S)


def pages():
    out = []
    for d, _, fs in os.walk(ROOT):
        for f in fs:
            if not f.endswith('.html') or 'OLD DO NOT USE' in f:
                continue
            p = os.path.join(d, f)
            rel = os.path.relpath(p, ROOT).replace('\\', '/')
            if rel != 'base.html' and re.search(
                    r'\{%\s*extends\s+["\']base\.html', read(p)):
                out.append((rel, p))
    return sorted(out)


BASE_PATH = os.path.join(ROOT, 'base.html')
BASE = read(BASE_PATH)
BASE_CSS = '\n'.join(styles_of(BASE))

# ==========================================================================
print('=' * 74)
print('1. BASE CARRIES THE RULE - ONCE, ON A PHONE, ON EVERY TEXT CONTROL')
print('=' * 74)
blocks = MARK.findall(BASE)
ok(len(blocks) == 1, 'base carries the ALV SMALL CONTROLS block once',
   'found %d' % len(blocks))
blk = COMMENT.sub('', blocks[0]) if blocks else ''
ok(re.search(r'@media\s+screen\s+and\s*\(max-width:\s*768px\)\s*\{', blk)
   is not None, 'inside a screen-only query at 768px - it never reaches paper')
rule = re.search(r'\{\s*([^{}]*?)\{\s*font-size\s*:\s*16px\s*!important\s*;'
                 r'?\s*\}', blk)
ok(rule is not None, 'the rule sets 16px !important and nothing else')
sels = [s.strip() for s in rule.group(1).split(',')] if rule else []
inp = [s for s in sels if s.startswith('input')]
ok('select' in sels and 'textarea' in sels and len(inp) == 1,
   'it reaches input, select and textarea', ', '.join(s[:30] for s in sels))
if inp:
    ok(all(':not([type="%s"])' % t in inp[0] for t in SKIP_TYPES),
       'and leaves out the %d input types iOS does not zoom on'
       % len(SKIP_TYPES))
    ok(re.fullmatch(r'input(:not\(\[type="\w+"\]\))+', inp[0]) is not None,
       'the input selector is ONE compound - no space inside the chain, '
       'which would make it a descendant selector matching nothing')
ok(re.search(r'\.form-control\s*\{\s*font-size\s*:\s*16px\s*;?\s*\}',
             COMMENT.sub('', BASE_CSS)) is not None,
   'CONTROL: the older .form-control guard is still there - two suites '
   'assert it')
if blocks:
    c = COMMENT.findall(blocks[0])
    ok(len(c) == 2 and not any('@' in x or 'font-size' in x for x in c),
       'the block\'s comments say nothing a CSS tool would read as CSS')
bak = BASE_PATH + SUFFIX
if os.path.isfile(bak):
    # LATER - test_print_buttons.py, 21 Sep. That round added its own
    # block to base, after this one. "base" here is base as it stood before
    # that round, when its backup is there, so this goes on judging only
    # its own block.
    _then = (read(BASE_PATH + '.bak_printbtn')
             if os.path.isfile(BASE_PATH + '.bak_printbtn') else BASE)
    ok(re.sub(r'\n\n' + MARK.pattern, '', _then, count=1, flags=re.S)
       == read(bak),
       'nothing else in base changed - base without the block is the backup')
else:
    skip('nothing else in base changed', 'no %s backup' % SUFFIX)

# ==========================================================================
print('\n' + '=' * 74)
print('2. dashboard_pl\'S YEAR SELECT LOST ONE WORD')
print('=' * 74)
DASH = os.path.join(ROOT, 'dashboard_pl.html')
if not os.path.isfile(DASH):
    skip('dashboard_pl.html', 'not in this checkout')
else:
    d = read(DASH)
    m = re.search(r'<select onchange="window\.location\.href=\'\?year=\''
                  r'[^>]*?style="([^"]*)"', d, re.S)
    ok(m is not None, 'the year select is where it was')
    if m:
        st = m.group(1)
        ok(re.search(r'font-size:\s*14px\s*;', st) is not None and
           not re.search(r'font-size:\s*14px\s*!important', st),
           'its inline font-size is 14px, no longer !important - so base '
           'can reach it on a phone and the desktop still reads 14px')
        ok(st.count('!important') >= 8,
           'every other inline !important on it is left alone',
           '%d left' % st.count('!important'))
    b = DASH + SUFFIX
    if os.path.isfile(b):
        was = read(b)
        # The page says `font-size: 14px !important;` three times; only the
        # year select's, the one with min-width after it, was the target.
        one = ('font-size: 14px !important;\n' + ' ' * 47 +
               'min-width: 120px !important;')
        # LATER - test_print_queries.py, 21 Sep. That round put `screen
        # and ` in front of this page's phone queries; the file is judged
        # as it stood before that round when its backup is there.
        then = (read(DASH + '.bak_printq')
                if os.path.isfile(DASH + '.bak_printq') else d)
        ok(was.count(one) == 1 and
           was.replace(one, one.replace(' !important;', ';', 1)) == then,
           'and that is the only change in the file - the other two '
           '14px !important on the page are untouched')
    else:
        skip('the only change in the file', 'no %s backup' % SUFFIX)

# ==========================================================================
print('\n' + '=' * 74)
print('3. THE INVARIANT - NO TEXT CONTROL UNDER 16px ON A PHONE')
print('=' * 74)
print("""
   Every page that extends base, rendered at 375 inside the real base CSS,
   Bootstrap 4.1.3 and the page's own styles. Controls built by script at
   runtime are not in the markup, and are not seen.
""")
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

MEASURE = r"""(skip) => {
  const out = [];
  document.querySelectorAll('input, select, textarea').forEach((e, i) => {
    const t = (e.getAttribute('type') || '').toLowerCase();
    if (skip.includes(t)) return;
    const s = getComputedStyle(e);
    out.push([i, e.tagName.toLowerCase(), t, (e.className || '').slice(0, 30),
              parseFloat(s.fontSize), s.paddingTop + ' ' + s.paddingRight]);
  });
  return out;
}"""


def fixture(boot, base_css, page_styles, markup):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, '
            'initial-scale=1"><title>s</title><style>%s</style>'
            '<style>%s</style>%s</head><body class="has-sidebar">'
            '<div class="main-content with-sidebar"><div>%s</div></div>'
            '</body></html>'
            % (boot, base_css, ''.join('<style>%s</style>' % c
                                       for c in page_styles), markup))


if sync_playwright is None or not os.path.isfile(BOOT):
    skip('the rendered invariant', 'playwright or %s missing' % BOOT)
    skip('the controls', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    base_now = BASE_CSS
    base_without = MARK.sub('', BASE_CSS)
    base_was = ('\n'.join(styles_of(read(bak))) if os.path.isfile(bak)
                else None)
    exe = '/opt/pw-browsers/chromium'
    n = [0]

    def render(br, html, width):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_sc_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': width, 'height': 900})
        # NOTHING LEAVES THE MACHINE. The markup carries real image and
        # font URLs; a suite that fetches them is slower, and on a flaky
        # line it fails for a reason that has nothing to do with CSS.
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(MEASURE, list(SKIP_TYPES))
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        all_pages = pages()
        small, measured, moved_ok, moved_bad, desk_bad = [], 0, 0, [], []
        was_small = 0
        for rel, p in all_pages:
            t = read(p)
            mk = body_markup(t)
            now = render(br, fixture(boot, base_now, styles_of(t), mk), 375)
            measured += len(now)
            small += ['%s %s.%s %gpx' % (rel, c[1], c[3] or c[2], c[4])
                      for c in now if c[4] < 16]
            if base_was is None:
                continue
            old_t = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else t
            old_mk = body_markup(old_t)
            before = render(br, fixture(boot, base_was, styles_of(old_t),
                                        old_mk), 375)
            if len(before) != len(now):
                moved_bad.append('%s: %d control(s) before, %d now'
                                 % (rel, len(before), len(now)))
                continue
            for x, y in zip(before, now):
                if x[4] < 16:
                    was_small += 1
                if x == y:
                    continue
                if x[4] < 16 and y[4] == 16 and x[5] == y[5]:
                    moved_ok += 1
                else:
                    moved_bad.append('%s %s.%s %gpx/%s -> %gpx/%s'
                                     % (rel, x[1], x[3] or x[2], x[4], x[5],
                                        y[4], y[5]))
            d_old = render(br, fixture(boot, base_was, styles_of(old_t),
                                       old_mk), 1280)
            d_now = render(br, fixture(boot, base_now, styles_of(t), mk),
                           1280)
            if len(d_old) != len(d_now) or d_old != d_now:
                diff = [(x, y) for x, y in zip(d_old, d_now) if x != y]
                desk_bad += ['%s %s.%s %gpx -> %gpx' % (rel, x[1], x[3] or
                                                        x[2], x[4], y[4])
                             for x, y in diff] or ['%s: control count' % rel]

        ok(len(all_pages) > 100 and measured > 0,
           'CONTROL: %d page(s) and %d text control(s) were measured'
           % (len(all_pages), measured))
        ok(not small, 'no text control on any page is under 16px at 375',
           '\n'.join(small[:8]))
        if base_was is None:
            skip('every control that moved was a small one',
                 'no base.html%s backup' % SUFFIX)
            skip('the desktop did not move', 'no base.html%s backup' % SUFFIX)
        else:
            ok(not moved_bad and moved_ok == was_small,
               'at 375, the %d control(s) that moved were exactly the %d '
               'that were small - to 16px, padding unchanged'
               % (moved_ok, was_small), '\n'.join(moved_bad[:8]))
            ok(not desk_bad, 'at 1280, every text control on every page is '
               'the size it was before the round', '\n'.join(desk_bad[:8]))
            notes.append('%d control(s) were under 16px at 375 before the '
                         'round and are 16px now.' % was_small)

        # ==================================================================
        print('\n' + '=' * 74)
        print('4. THE CONTROLS - A FIXTURE OF OUR OWN, SO THEY NEVER EXPIRE')
        print('=' * 74)
        FX = ('<style>.x { font-size: 13px; }</style>'
              '<input class="x" type="text"><select class="x"></select>'
              '<textarea class="x"></textarea>'
              '<input type="number" style="font-size: 12px">'
              '<input type="date" style="font-size: 14px">')
        mk = body_markup('{% block content %}' + FX + '{% endblock %}')
        styles = ['.x { font-size: 13px; }']
        phone = render(br, fixture(boot, base_now, styles, mk), 375)
        desk = render(br, fixture(boot, base_now, styles, mk), 1280)
        gone = render(br, fixture(boot, base_without, styles, mk), 375)
        ok(len(phone) == 5 and all(c[4] == 16 for c in phone),
           'a page rule, two inline styles, a select and a textarea - all '
           '16px on a phone', ', '.join('%s %g' % (c[1], c[4]) for c in phone))
        ok(sorted(c[4] for c in desk) == [12, 13, 13, 13, 14],
           'and exactly what the page asked for on the desktop',
           ', '.join('%s %g' % (c[1], c[4]) for c in desk))
        ok(len(gone) == 5 and all(c[4] < 16 for c in gone),
           'CONTROL: with the rule taken back out of base they are small '
           'again - section 3 can see a failure',
           ', '.join('%s %g' % (c[1], c[4]) for c in gone))
        cb = render(br, fixture(boot, base_now, [], '<input type="checkbox" '
                                'style="font-size: 12px">'), 375)
        ok(cb == [], 'a checkbox is not a text control, and is not measured')
        chk = br.new_context(viewport={'width': 375, 'height': 900})
        chk.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = chk.new_page()
        fx = os.path.join(SCRATCH, '_sc_cb.html')
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(fixture(boot, base_now, [], '<input type="checkbox" '
                            'style="font-size: 12px">'))
        _goto(pg, fx)
        cbs = pg.evaluate("() => getComputedStyle(document.querySelector("
                          "'input')).fontSize")
        chk.close()
        ok(cbs == '12px', 'and base leaves it alone - it stays 12px', cbs)
        imp = render(br, fixture(boot, base_now, [], '<input type="text" '
                                 'style="font-size: 12px !important">'), 375)
        ok(len(imp) == 1 and imp[0][4] == 12,
           'CONTROL: an inline !important beats base - the one thing it '
           'cannot reach - and the scan in section 3 sees it at 12px',
           str(imp))
        br.close()

# ==========================================================================
print('\n' + '=' * 74)
print('5. IT IS ON THE GATE')
print('=' * 74)
if os.path.isfile(PS1):
    ps = read(PS1)
    i = ps.find('$suites = @(')
    j = ps.find('\n)', i)
    ok(i >= 0 and "'%s'" % ME in ps[i:j],
       '%s runs %s on every push' % (PS1, ME))
else:
    skip('the gate', '%s not on disk' % PS1)

# ==========================================================================
print('\n' + '=' * 74)
if notes:
    print('NOTED, NOT FAILED')
    for x in notes:
        print('  - ' + x)
    print('')
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
