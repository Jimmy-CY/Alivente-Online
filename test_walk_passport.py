# -*- coding: utf-8 -*-
"""test_walk_passport.py - Section W round W1, 28 Sep 2026.

The first round whose findings came from Demetri walking the system.

SECTION 1 IS THE ONE THAT MATTERS. The page's row order was being set by
a select that only the phone could see. The view said
`order_by('-created_at')`; the template then ran
`applyMobileSort('expiry-asc')` inside a DOMContentLoaded with no width
guard, against a control CSS hid above 768px but never removed from the
DOM. Deleting the control alone would have silently reverted the desktop
table to newest-added-first. The ordering moved into the view instead,
and this section holds it there.

SECTION 5 IS RENDERED at both widths, because the primary moving into
the action bar changes what fits on a phone.

NOT CLAIMED HERE: that the desktop row buttons were ever wrong. They
were reported as filled teal/amber/red; they measure as base's outlined
.icon-action-btn and always did in this code. That was a cached page,
and section 5 measures it so the next reader does not go looking.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import ast
import os
import re
import sys

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
V = os.path.join(ROOT, 'pages', 'views')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_walk1'
ME = 'test_walk_passport.py'
PATCHER = 'apply_walk_passport.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
PAGE = os.path.join(T, 'passport_management.html')
VIEW = os.path.join(V, 'passports.py')

# The four hexes, and what each now reads instead.
COLOURS = [('.icon-color-view', '#0e7c8b', '--alv-view'),
           ('.icon-color-edit', '#ffc107', '--alv-edit'),
           ('.icon-color-delete', '#dc3545', '--alv-danger'),
           ('.icon-color-upload', '#007bff', '--alv-edit')]
# What the four render as once they read the tokens.
RENDERS = {'view': 'rgb(14, 124, 139)', 'edit': 'rgb(37, 99, 235)',
           'delete': 'rgb(179, 38, 30)'}
# Names that must not survive anywhere in the template.
DEAD = ['mobile-sort-control', 'mobile-sort-label', 'mobile-sort-select',
        'mobileSortSelect', 'applyMobileSort', 'add-new-button-row',
        'action-btn-add']

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


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def bare(s):
    """Selector name with CSS comments stripped - lesson 21, which this
    round's own patcher forgot once and paid a false failure for: the
    four icon rules sit under a `/* Icon colours */ ` banner, and the
    rule pattern hands that banner to the first selector."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def css_of(t):
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return '\n'.join(STYLE.findall(raw))


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def body_for(sel, css):
    for m in RULE.finditer(css):
        if bare(m.group(1)) == sel:
            return m.group(2)
    return None


def one_branch(t):
    while True:
        stack = []
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                stack.append([m.start(), m.end(), None])
            elif k in ('elif', 'else'):
                if stack and stack[-1][2] is None:
                    stack[-1][2] = m.start()
            elif k == 'endif':
                if not stack:
                    return t
                s, fe, cut = stack.pop()
                if cut is not None:
                    t = t[:s] + t[fe:cut] + t[m.end():]
                    break
        else:
            return t


def body_of(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '42', b, flags=re.S)


print('=' * 74)
print('%s - W1, PASSPORT MANAGEMENT' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE ORDERING LIVES IN THE VIEW NOW, NOT IN A HIDDEN SELECT')
# ==========================================================================
vn, vw = now(VIEW), was(VIEW)
ok(bool(vn), 'views/passports.py is here to check', VIEW)
try:
    ast.parse(vn)
    ok(True, '  and it parses')
except SyntaxError as e:
    ok(False, '  and it parses', e)
ok('from django.db.models import F' in vn, '  it imports F')
ok("F('expiry_date').asc(nulls_last=True)" in vn,
   '  and orders by expiry, soonest first, undated LAST')
ok("'-created_at'" in vn,
   '  keeping -created_at as the tie-break, so equal expiries hold their '
   'old order')
ok("order_by('-created_at')" in vw and "order_by('-created_at')" not in vn,
   "CONTROL: the view really did order by '-created_at' before")
ok('applyMobileSort' in was(PAGE),
   '  and the TEMPLATE really did re-sort it afterwards')
ok(re.search(r'applyMobileSort\([^)]*\)\s*;', was(PAGE)) is not None,
   '  called unconditionally, with no width guard - which is how a phone '
   'control came to order the desktop')

# ==========================================================================
head('2. THE PHONE SORT CONTROL IS GONE, THE METADATA IS NOT')
# ==========================================================================
tn, tw = now(PAGE), was(PAGE)
for d in DEAD:
    ok(d not in tn, '%-22s is gone' % d)
    ok(d in tw, '  CONTROL: it was there before' if d == DEAD[0] else
       '  (and was there before)')
ok('data-sort-value' in tn and 'data-sort-key' in tn,
   'data-sort-key / data-sort-value are KEPT - the filter round wants '
   'them, and the desktop header sort never used them')
ok('cell.textContent' in tn or 'textContent' in tn,
   '  CONTROL: the desktop header sort reads textContent, which is why '
   'that metadata was only ever the phone sort\'s')

# ==========================================================================
head('3. THE PRIMARY IS IN THE BAR')
# ==========================================================================
mk = re.sub(r'<(script|style)\b.*?</\1>', '', tn, flags=re.S | re.I)
i = mk.index('<div class="page-action-buttons">')
bar = mk[i:mk.index('</div>', mk.index('action-back', i))]
ok('action-primary' in bar, 'the bar contains the primary')
ok(bar.index('action-primary') < bar.index('action-secondary'),
   '  first, before the secondaries')
ok('Add New Passport/ID' in bar, '  and it is Add New Passport/ID')
mkw = re.sub(r'<(script|style)\b.*?</\1>', '', tw, flags=re.S | re.I)
j = mkw.index('<div class="page-action-buttons">')
barw = mkw[j:mkw.index('</div>', mkw.index('action-back', j))]
ok('action-primary' not in barw,
   'CONTROL: it was NOT in the bar before - it had a row of its own below')
ok('disabled-btn' in bar,
   '  and the no-permission branch uses base\'s .disabled-btn rather than '
   'a live-looking span')

# ==========================================================================
head('4. FOUR HEXES READ TOKENS')
# ==========================================================================
cn, cw = css_of(tn), css_of(tw)
for sel, hexv, tok in COLOURS:
    bn, bw2 = body_for(sel, cn), body_for(sel, cw)
    ok(bn is not None and 'var(%s)' % tok in bn,
       '%-20s reads var(%s)' % (sel, tok), bn)
    ok(bw2 is not None and hexv in bw2,
       '  CONTROL: it read %s before' % hexv)
ok('#0e7c8b' in cn,
   'and the round left the page\'s OTHER hexes alone - the hex sweep '
   'takes all 119 pages after the walkthrough, not one page of it here')

# ==========================================================================
head('5. RENDERED - BOTH WIDTHS, BECAUSE THE BAR GAINED A CONTROL')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = '\n'.join(styles_of(read(BASE)))


def fixture(page_text):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div></body></html>'
            % (boot, bcss,
               ''.join('<style>%s</style>' % c for c in styles_of(page_text)),
               body_of(page_text)))


PROBE = """() => {
  const bar = document.querySelector('.page-action-buttons');
  const kids = Array.from(bar.children).map(e => {
    const r = e.getBoundingClientRect();
    return {cls: e.className.replace('btn ', ''), w: Math.round(r.width),
            left: Math.round(r.left), right: Math.round(r.right),
            vis: r.width > 0 && r.height > 0};
  });
  const ink = {};
  for (const k of ['view', 'edit', 'delete']) {
    const e = document.querySelector('.icon-color-' + k);
    ink[k] = e ? getComputedStyle(e).color : 'absent';
  }
  const row = document.querySelector('.icon-action-btn.icon-edit');
  return {kids: kids, ink: ink,
          sortSelect: !!document.getElementById('mobileSortSelect'),
          rowBg: row ? getComputedStyle(row).backgroundColor : 'absent',
          rowInk: row ? getComputedStyle(row).color : 'absent'};
}"""


def shoot(text, width):
    from playwright.sync_api import sync_playwright
    fx = os.path.join(SCRATCH, 'w1_%d.html' % width)
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(fixture(text))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': width, 'height': 800})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        out = pg.evaluate(PROBE)
        br.close()
    return out


if not HAVE:
    skip('the rendered probe', 'playwright is not installed')
else:
    for width, want in ((390, 4), (1280, 4)):
        r = shoot(tn, width)
        kids = r['kids']
        ok(len(kids) == want,
           'at %4dpx the bar holds %d controls' % (width, len(kids)),
           kids)
        ok(all(k['vis'] for k in kids),
           '  and every one of them is visible', kids)
        ok(kids[0]['cls'].startswith('action-primary'),
           '  the primary is first (%dpx)' % kids[0]['w'])
        ok(kids[-1]['cls'].startswith('action-back'),
           '  and Back is last, flush right at %d of %d'
           % (kids[-1]['right'], width))
        ok(kids[-1]['right'] <= width,
           '  nothing runs off the end')
        overlaps = [(a['cls'], b['cls']) for a, b in zip(kids, kids[1:])
                    if b['left'] < a['right']]
        ok(not overlaps, '  and nothing overlaps', overlaps)
        ok(not r['sortSelect'], '  no sort select in the DOM at all')

    r = shoot(tn, 390)
    for k, want in RENDERS.items():
        ok(r['ink'][k] == want,
           '  .icon-color-%-7s renders %s' % (k, want), r['ink'][k])
    w = shoot(tw, 390)
    ok(w['ink']['edit'] == 'rgb(255, 193, 7)',
       'CONTROL: the Edit icon really was Bootstrap amber', w['ink']['edit'])
    ok(w['ink']['view'] == r['ink']['view'],
       '  and View does NOT change - its hex already equalled the token, '
       'so naming it is a correctness fix, not a visible one')

    # THE ONE THAT WAS REPORTED AND IS NOT A DEFECT.
    d = shoot(tn, 1280)
    ok(d['rowBg'] == 'rgb(255, 255, 255)',
       'the DESKTOP row buttons are base\'s outlined style, not filled',
       d['rowBg'])
    ok(d['rowInk'] == 'rgb(37, 99, 235)',
       '  with --alv-edit ink - so the filled amber in the screenshot was '
       'a cached page, not this code', d['rowInk'])

# ==========================================================================
head('6. CONTROLS, AND THE GATE')
# ==========================================================================
ok(bare('/* Icon colours */ .icon-color-view') == '.icon-color-view',
   'the selector reader strips a comment banner (lesson 21)')
ok(body_for('.icon-color-edit', cn) is not None,
   '  and finds a rule that carries one')
ok('applyMobileSort' in was(PAGE),
   'reverting the page puts the sort back, so section 2 would FAIL')
ok("order_by('-created_at')" in was(VIEW),
   '  and reverting the view puts -created_at back, so section 1 would '
   'FAIL too')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_lastmenu' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_lastmenu'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  WORTH A LOOK, NOT FIXED HERE: this page has no More menu, so its')
print('  Help button stays in the bar on a phone and the primary gets')
print('  177px of 390 rather than the whole row. Thirty-two pages have a')
print('  More menu and would put Help inside it. That is a judgement about')
print('  this page, not a defect, so it is written down rather than done.')
print('=' * 74)
sys.exit(1 if failed else 0)
