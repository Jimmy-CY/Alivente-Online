# -*- coding: utf-8 -*-
"""test_print_buttons.py - no button reaches paper except one that is
content, and nothing but buttons left the printed page.

    python test_print_buttons.py

Run from the repo root. Paired with apply_print_buttons.py (21 Sep).

  1. base carries the print rule once - buttons, .btn and the three button
     input types, display none on paper, unless .print-keep.
  2. home's six dashboard rows are marked .print-keep, and nothing else in
     the file changed.
  3. RENDERED, every page that extends base, printed at 718 (A4 portrait):
     no visible button but a .print-keep one. Against the backups, every
     element that left the printed page was a button or inside one - so
     nothing else moved. On screen, at 375 and 1280, nothing moved at all.
  4. CONTROLS, on a fixture of our own: a button, a .btn link and a submit
     vanish on paper and stay on screen; a .print-keep button, a plain
     link and a badge print. And home with its marks stripped must print
     its dashboard rows NOT at all - or section 3 proves nothing about them.
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

SUFFIX = '.bak_printbtn'
BOOT = 'test_fixture_bootstrap413.css'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_print_buttons.py'
KEEP = 'print-keep'
MARK = re.compile(r'/\* ALV PRINT BUTTONS v1\b.*?/\* /ALV PRINT BUTTONS v1 \*/',
                  re.S)
COMMENT = re.compile(r'/\*.*?\*/', re.S)
BTN = ('button, .btn, input[type=submit], input[type=button], '
       'input[type=reset]')

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
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def body_markup(t):
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
HOME = os.path.join(ROOT, 'home.html')

# ==========================================================================
print('=' * 74)
print('1. BASE CARRIES THE PRINT RULE ONCE')
print('=' * 74)
blocks = MARK.findall(BASE)
ok(len(blocks) == 1, 'base carries the ALV PRINT BUTTONS block once',
   'found %d' % len(blocks))
blk = ' '.join(COMMENT.sub('', blocks[0]).split()) if blocks else ''
ok(blk.startswith('@media print {'), 'inside @media print - paper only')
m = re.search(r'\{\s*([^{}]*)\{\s*display\s*:\s*none\s*!important\s*;?\s*\}',
              blk)
sels = [s.strip() for s in m.group(1).split(',')] if m else []
want = ['button:not(.print-keep)', '.btn:not(.print-keep)',
        'input[type="submit"]', 'input[type="button"]', 'input[type="reset"]']
ok(sels == want, 'it hides button, .btn and the three button inputs, '
   'except .print-keep', ', '.join(sels))
if blocks:
    c = COMMENT.findall(blocks[0])
    ok(len(c) == 2 and not any('@' in x or 'display' in x for x in c),
       'the block\'s comments say nothing a CSS tool would read as CSS')
bak = BASE_PATH + SUFFIX
if os.path.isfile(bak):
    ok(re.sub(r'\n\n' + MARK.pattern, '', BASE, count=1, flags=re.S)
       == read(bak), 'nothing else in base changed')
else:
    skip('nothing else in base changed', 'no %s backup' % SUFFIX)

# ==========================================================================
print('\n' + '=' * 74)
print('2. home\'S DASHBOARD ROWS ARE CONTENT, AND SAY SO')
print('=' * 74)
h = read(HOME)
rows = re.findall(r'<button\b[^>]*class="([^"]*\btoday-row\b[^"]*)"', h)
ok(len(rows) >= 6 and all(KEEP in r.split() for r in rows),
   'every one of home\'s %d insight rows carries .print-keep' % len(rows),
   '\n'.join(r for r in rows if KEEP not in r.split()))
keeps = [(rel, len(re.findall(r'class="[^"]*\bprint-keep\b', read(p))))
         for rel, p in pages()]
keeps = [(r, k) for r, k in keeps if k]
ok(keeps == [('home.html', len(rows))],
   'and home is the only page that keeps a button on paper',
   ', '.join('%s %d' % x for x in keeps))
if os.path.isfile(HOME + SUFFIX):
    ok(h.replace(' ' + KEEP + '"', '"') == read(HOME + SUFFIX),
       'and the class is the only change in home.html')
else:
    skip('the only change in home.html', 'no %s backup' % SUFFIX)

# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

SEEN = r"""(btn) => {
  const all = Array.from(document.querySelectorAll('body *'));
  return all.map(e => [e.checkVisibility(), !!e.closest(btn),
                       e.tagName.toLowerCase() + '.' +
                       String(e.className || '').trim().split(/\s+/)
                         .slice(0, 2).join('.'),
                       !!e.closest('.print-keep'), e.matches(btn)]);
}"""
SNAP = r"""() => Array.from(document.querySelectorAll('body *')).map(e => {
  const s = getComputedStyle(e);
  return [e.checkVisibility(), s.display, s.fontSize,
          Math.round(e.getBoundingClientRect().width)]; })"""


def fixture(boot, base_css, page_styles, markup):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<title>b</title><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar"><div>%s</div></div></body></html>'
            % (boot, base_css, ''.join('<style>%s</style>' % c
                                       for c in page_styles), markup))


print('\n' + '=' * 74)
print('3. RENDERED - NO BUTTON ON PAPER, AND NOTHING ELSE LEFT IT')
print('=' * 74)
if sync_playwright is None or not os.path.isfile(BOOT):
    skip('3 and 4', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    base_now = '\n'.join(styles_of(BASE))
    base_was = '\n'.join(styles_of(read(bak))) if os.path.isfile(bak) \
        else None
    exe = '/opt/pw-browsers/chromium'
    n = [0]

    def render(br, html, w, media, js, arg=None):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_pb_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 1000})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        pg.emulate_media(media=media)
        _goto(pg, fx)
        r = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        on_paper, others, went, screen_moved = [], [], 0, []
        all_pages = pages()
        for rel, p in all_pages:
            t = read(p)
            mk = body_markup(t)
            now = render(br, fixture(boot, base_now, styles_of(t), mk), 718,
                         'print', SEEN, BTN)
            on_paper += ['%s %s' % (rel, e[2]) for e in now
                         if e[0] and e[4] and not e[3]]
            if base_was is None:
                continue
            old_t = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else t
            old_mk = body_markup(old_t)
            was = render(br, fixture(boot, base_was, styles_of(old_t),
                                     old_mk), 718, 'print', SEEN, BTN)
            if len(was) != len(now):
                others.append('%s: %d elements before, %d now'
                              % (rel, len(was), len(now)))
                continue
            for x, y in zip(was, now):
                if x[0] == y[0]:
                    continue
                if x[0] and not y[0] and y[1]:
                    went += 1
                else:
                    others.append('%s %s %s' % (rel, y[2], 'appeared'
                                                if y[0] else 'vanished'))
            for w in (375, 1280):
                a = render(br, fixture(boot, base_was, styles_of(old_t),
                                       old_mk), w, 'screen', SNAP)
                b = render(br, fixture(boot, base_now, styles_of(t), mk), w,
                           'screen', SNAP)
                if a != b:
                    screen_moved.append('%s at %d' % (rel, w))
        ok(len(all_pages) > 100, 'CONTROL: %d page(s) printed'
           % len(all_pages))
        ok(not on_paper, 'no page prints a button but a .print-keep one',
           '\n'.join(on_paper[:8]))
        if base_was is None:
            skip('only buttons left the page', 'no base.html%s backup'
                 % SUFFIX)
            skip('the screen did not move', 'no base.html%s backup' % SUFFIX)
        else:
            ok(went > 0 and not others,
               '%d element(s) left the printed pages, every one a button or '
               'inside one - nothing else moved' % went,
               '\n'.join(others[:8]))
            ok(not screen_moved, 'on screen, at 375 and 1280, every page '
               'renders exactly as it did', '\n'.join(screen_moved[:8]))

        # ==================================================================
        print('\n' + '=' * 74)
        print('4. THE CONTROLS')
        print('=' * 74)
        FX = ('<button id="b1">Save</button><a id="b2" class="btn" href="#">'
              'Back</a><input id="b3" type="submit" value="Go">'
              '<button id="k1" class="print-keep">3 overdue</button>'
              '<a id="l1" href="#">a link</a>'
              '<span id="s1" class="badge badge-info">Paid</span>'
              '<input id="t1" type="text" value="typed">')
        IDS = ['b1', 'b2', 'b3', 'k1', 'l1', 's1', 't1']
        VIS = """(ids) => ids.map(i =>
            document.getElementById(i).checkVisibility())"""
        paper = render(br, fixture(boot, base_now, [], FX), 718, 'print',
                       VIS, IDS)
        screen = render(br, fixture(boot, base_now, [], FX), 718, 'screen',
                        VIS, IDS)
        ok(paper == [False, False, False, True, True, True, True],
           'on paper: a button, a .btn link and a submit go; a print-keep '
           'button, a link, a badge and a text box stay',
           dict(zip(IDS, paper)))
        ok(all(screen), 'on screen every one of them is there',
           dict(zip(IDS, screen)))
        gone = render(br, fixture(boot, MARK.sub('', base_now), [], FX), 718,
                      'print', VIS, IDS)
        ok(all(gone), 'CONTROL: with the rule taken out of base, all of them '
           'print - the check above can fail', dict(zip(IDS, gone)))
        stripped = h.replace(' ' + KEEP + '"', '"')
        rows_js = """() => Array.from(document.querySelectorAll(
            'button.today-row')).map(e => e.checkVisibility())"""
        kept = render(br, fixture(boot, base_now, styles_of(h),
                                  body_markup(h)), 718, 'print', rows_js)
        lost = render(br, fixture(boot, base_now, styles_of(stripped),
                                  body_markup(stripped)), 718, 'print',
                      rows_js)
        ok(kept and all(kept), 'home prints its %d dashboard rows'
           % len(kept), str(kept))
        ok(lost and not any(lost), 'CONTROL: with print-keep stripped, home '
           'would print its cards empty - the mark is doing the work',
           str(lost))
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

print('\n' + '=' * 74)
if notes:
    print('NOTED, NOT FAILED')
    for x in notes:
        print('  - ' + x)
    print('')
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
