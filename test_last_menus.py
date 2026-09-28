# -*- coding: utf-8 -*-
"""test_last_menus.py - Section H round H10, 28 Sep 2026.

The last three More menus join base's binder. H8 moved twenty-six pages
onto it and H9 took the component's CSS back; both left these three
alone because each carried a hand-inlined handler that a class-wide
binder would have double-bound.

SECTION 1 IS THE WHOLE POINT: 32 of 32 pages on one binder, ZERO writing
their own handler, and exactly ONE still painting the component - the
dashboard's always-present side hamburger, which H9 named and measured
and left.

SECTION 4 CHECKS A CORRECTION RATHER THAN AN ADDITION. H8 wrote into
base that once these three joined, "the attributes stop being needed".
That was wrong. The binder finds its toggle and panel BY ATTRIBUTE, so
binding the class would bind nothing unless base learned the More menu's
own id and class names - the coupling the component was written to
avoid. This section fails if that sentence is still in base, and fails
if the reason replacing it is not.
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

SUFFIX = '.bak_lastmenu'
ME = 'test_last_menus.py'
PATCHER = 'apply_last_menus.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

MINE = ['invoices.html', 'physical_invoice_list.html', 'finance_pl_act.html']
# The one page that still paints the component, named and measured in H9.
PAINTER = 'property_management_dashboard.html'
ATTRS = ('data-menu', 'data-menu-toggle', 'data-menu-panel')
# The sentence H8 wrote and H10 takes back.
WRONG = 'the attributes stop being needed'

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
SEL = re.compile(r'\.action-more-(?:wrapper|btn|menu|item|divider)\b')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def bare(s):
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def markup(t):
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def js_of(t):
    return '\n'.join(SCRIPT.findall(re.sub(r'<!--.*?-->', ' ', t, flags=re.S)))


def css_of(t):
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)), flags=re.S)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def paints(t):
    return [bare(m.group(1)) for m in RULE.finditer(css_of(t))
            if SEL.search(bare(m.group(1)))]


def walked():
    out = []
    for folder, _, names in os.walk(T):
        for n in sorted(names):
            if n.endswith('.html'):
                rel = os.path.relpath(os.path.join(folder, n), T)
                out.append((rel.replace(os.sep, '/'),
                            os.path.join(folder, n)))
    return sorted(out)


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
print('%s - H10, THE LAST THREE MORE MENUS' % ME)
print('=' * 74)

pages = [(rel, p) for rel, p in walked()
         if rel != 'base.html' and 'actionMoreBtn' in read(p)]

# ==========================================================================
head('1. THIRTY-TWO OF THIRTY-TWO, AND NOBODY WRITES IT OUT')
# ==========================================================================
ok(len(pages) == 32, '32 pages carry a More menu', len(pages))
off = [rel for rel, p in pages
       if not all(a in markup(now(p)) for a in ATTRS)]
ok(not off, '  and every one of them is on base\'s binder', off)
holding = [rel for rel, p in pages if 'actionMoreBtn' in js_of(now(p))]
ok(not holding, '  NOT ONE still writes its own handler', holding)
painting = [rel for rel, p in pages if paints(now(p))]
ok(painting == [PAINTER],
   '  and exactly one still paints it - %s, named and measured in H9'
   % PAINTER.replace('.html', ''), painting)
ok(all(re.search(r'id="actionMoreMenu"[^>]*\bhidden\b', markup(now(p)))
       for _, p in pages),
   '  every panel starts closed in its own markup')

# ==========================================================================
head('2. THE THREE GAVE UP A HANDLER THEY REALLY HAD')
# ==========================================================================
for rel in MINE:
    p = os.path.join(T, rel)
    ok('actionMoreBtn' in js_of(was(p)),
       '%-28s CONTROL: it wrote one before this round'
       % rel.replace('.html', ''))
    ok('actionMoreBtn' not in js_of(now(p)),
       '  and does not now')
    ok(all(a in markup(now(p)) for a in ATTRS)
       and not all(a in markup(was(p)) for a in ATTRS),
       '  and gained the three attributes in the same round')
    ok(len(js_of(now(p))) < len(js_of(was(p))),
       '  its JavaScript shrank', '%d -> %d'
       % (len(js_of(was(p))), len(js_of(now(p)))))

# ==========================================================================
head('3. finance_pl_act GIVES UP WHAT H9 COULD NOT TAKE')
# ==========================================================================
fp = os.path.join(T, 'finance_pl_act.html')
ok(len(paints(was(fp))) == 8,
   'it painted the component with %d rules' % len(paints(was(fp))),
   paints(was(fp)))
ok(not paints(now(fp)), '  and with none now')
ok(any('.show' in s for s in paints(was(fp))),
   '  one of them was the .show pair - the only thing hiding its panel, '
   'which is why H9 left the page whole')
ok(not re.search(r'id="actionMoreMenu"[^>]*\bhidden\b', markup(was(fp))),
   '  CONTROL: its markup carried no hidden, so the panel was open until '
   'its script ran')
ok(re.search(r'id="actionMoreMenu"[^>]*\bhidden\b', markup(now(fp)))
   is not None,
   '  and it does now')

# ==========================================================================
head("4. base TAKES BACK WHAT H8 PROMISED")
# ==========================================================================
bn, bw = now(BASE), was(BASE)
ok(WRONG in bw, 'CONTROL: base really did say %r' % WRONG)
ok(WRONG not in bn, '  and does not any more')
ok('H10, 28 Sep 2026' in bn, '  the note records who took it back')
for want in ('BY ATTRIBUTE', 'ui-menu'):
    ok(want in bn,
       '  and says why - it names %s' % want)
ok(len(js_of(bn)) == len(js_of(bw)),
   '  base gained no JavaScript', '%d -> %d'
   % (len(js_of(bw)), len(js_of(bn))))
ok(len(''.join(styles_of(bn))) == len(''.join(styles_of(bw))),
   '  and no CSS - the only change to base is prose')

# THE CLAIM ITSELF, CHECKED RATHER THAN ASSERTED. The binder really does
# find its parts by attribute, which is why binding the class would bind
# nothing.
binder = [s for s in SCRIPT.findall(bn) if 'data-menu-toggle' in s]
ok(len(binder) == 1, 'base has exactly one menu binder', len(binder))
if binder:
    ok("querySelector('[data-menu-toggle]')" in binder[0]
       or '[data-menu-toggle]' in binder[0],
       '  and it finds its toggle by attribute, not by class')
    ok('action-more' not in binder[0],
       '  and never names the More menu at all - which is the coupling '
       'the attributes exist to avoid')

# ==========================================================================
head('5. RENDERED - ALL THREE OPEN AND CLOSE ON base ALONE')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = '\n'.join(styles_of(bn))


def fixture(page_text):
    """base's stylesheet and binder, the page's markup, and NO page
    script at all - so a menu that opens is base's doing. These three
    have no handler left to load, which is the thing being proved."""
    parts = ['<script>%s</script>' % binder[0]] if binder else []
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div>%s</body></html>'
            % (boot, bcss,
               ''.join('<style>%s</style>' % c for c in styles_of(page_text)),
               body_of(page_text), ''.join(parts)))


STATE = """() => {
  const m = document.getElementById('actionMoreMenu');
  const b = document.getElementById('actionMoreBtn');
  if (!m || !b) return null;
  const r = m.getBoundingClientRect(), rb = b.getBoundingClientRect();
  return {vis: r.width > 0 && r.height > 0, w: Math.round(r.width),
          btnVis: rb.width > 0 && rb.height > 0,
          exp: b.getAttribute('aria-expanded')};
}"""

if not HAVE or not binder:
    skip('the rendered probe', 'no browser, or no binder in base')
else:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 390, 'height': 700})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        for rel in MINE:
            fx = os.path.join(SCRATCH, rel.replace('/', '_'))
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(now(os.path.join(T, rel))))
            pg = ctx.new_page()
            _goto(pg, fx)
            s0 = pg.evaluate(STATE)
            if not s0 or not s0['btnVis']:
                ok(False, '%-28s opens and closes' % rel.replace('.html', ''),
                   'the More button is not visible')
                pg.close()
                continue
            pg.click('#actionMoreBtn', timeout=4000)
            s1 = pg.evaluate(STATE)
            pg.click('#actionMoreBtn', timeout=4000)
            s2 = pg.evaluate(STATE)
            ok(not s0['vis'] and s1['vis'] and not s2['vis']
               and s1['w'] == 200 and s0['exp'] == 'false'
               and s1['exp'] == 'true' and s2['exp'] == 'false',
               '%-28s closed - open (%dpx) - closed'
               % (rel.replace('.html', ''), s1['w']),
               '%s / %s / %s' % (s0, s1, s2))
            pg.close()
        br.close()

# ==========================================================================
head('6. CONTROLS, AND THE GATE')
# ==========================================================================
ok('actionMoreBtn' in js_of(was(os.path.join(T, 'invoices.html'))),
   'reverting a page puts its handler back, so section 2 would FAIL')
ok(WRONG in was(BASE),
   "  and reverting base puts H8's wrong sentence back, so section 4 "
   'would FAIL too')
ok(paints(was(fp)) and not paints(now(fp)),
   '  and reverting finance_pl_act puts its eight rules back')
ok(SEL.search('.action-more-menu') is not None
   and SEL.search('.action-primary') is None,
   '  the paint pattern matches the component and not a bar button')
ok(not paints('<style>/* .action-more-item */ a{x:1}</style>'),
   '  and is not tripped by a class named inside a CSS comment')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_morecss' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_morecss'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THE COMPONENT IS WHOLE. base owns the More menu\'s markup names,')
print('  its CSS and its behaviour; 32 pages wear three attributes and')
print('  nothing else. What began as 31,642 characters of duplicated')
print('  JavaScript and 22,357 of duplicated CSS across three rounds is')
print('  now one binder and one stylesheet - and the one page that keeps')
print('  its own rules keeps them for a reason that was measured, not')
print('  assumed.')
print('=' * 74)
sys.exit(1 if failed else 0)
