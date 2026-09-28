# -*- coding: utf-8 -*-
"""test_more_css.py - Section H round H9, 28 Sep 2026.

H8 took the More menu's BEHAVIOUR. This takes its PAINT: twenty-four
pages give up 22,357 characters of .action-more-* CSS for a component
base has styled since the action-bar round.

SECTION 2 IS THE LESSON. Most of that CSS NEVER APPLIED. base scopes its
button rule as `.page-action-buttons .action-more-btn`, which is (0,2,0);
a page's bare `.action-more-btn` is (0,1,0) and loses however late in the
document it sits. asset_detail.html measures zero difference either way -
its whole local copy was already dead.

SECTION 4 IS THE DRIFT, IN ONE NUMBER. The icon inside a More-menu item
was written in THREE different colours across five pages - Bootstrap
green #28a745, red #dc3545 and amber #ffc107 - with three more pages
setting none at all, and not one of those eight menus holds a
destructive action. They are Help, Nutrition, Shopping List, Print
Recipe, Edit, Duplicate, Missing Conversions. base says --alv-accent.

SECTIONS 5 AND 6 ARE RENDERED, and section 6 is why this round has two
exclusions rather than none. It STRIPS the local rules from the two
excluded pages inside the fixture and measures what that does:

    property_management_dashboard  44x47 -> 26x14 on a phone, and
                                   56x36 -> GONE on a desktop
    finance_pl_act                 the closed panel renders OPEN

Neither is drift. The dashboard's menu is an always-present side
hamburger outside any .page-action-buttons, which is a component base
does not have; finance_pl_act is one of the three pages still on a
hand-inlined handler, and its .show pair is the only thing hiding its
panel.
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

SUFFIX = '.bak_morecss'
ME = 'test_more_css.py'
PATCHER = 'apply_more_css.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

SKIP = {
    'property_management_dashboard.html':
        'an always-present side hamburger, outside any .page-action-buttons',
    'finance_pl_act.html':
        'its .show pair is the only thing hiding the panel',
}
# What base draws the menu as, once the local copies are gone.
HOUSE_MENU_WIDTH = 200

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


def css_of(t):
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)), flags=re.S)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def more_rules(t):
    return [bare(m.group(1)) for m in RULE.finditer(css_of(t))
            if SEL.search(bare(m.group(1)))]


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


def walked():
    out = []
    for folder, _, names in os.walk(T):
        for n in sorted(names):
            if n.endswith('.html'):
                rel = os.path.relpath(os.path.join(folder, n), T)
                out.append((rel.replace(os.sep, '/'),
                            os.path.join(folder, n)))
    return sorted(out)


print('=' * 74)
print("%s - H9, THE MORE MENU'S CSS GOES HOME" % ME)
print('=' * 74)

mine = [(rel, p) for rel, p in walked()
        if rel != 'base.html' and rel not in SKIP
        and os.path.isfile(p + SUFFIX)]

# ==========================================================================
head('1. THE CENSUS')
# ==========================================================================
ok(len(mine) == 24, '24 pages gave up their copy', len(mine))
gone = sum(len(was(p)) - len(now(p)) for _, p in mine)
ok(gone > 21000, '  %d characters of duplicated CSS removed' % gone, gone)
for rel, why in sorted(SKIP.items()):
    ok(os.path.isfile(os.path.join(T, rel))
       and not os.path.isfile(os.path.join(T, rel) + SUFFIX),
       '  %s was not touched - %s' % (rel.replace('.html', ''), why))
ok(any(rel.startswith('projects/') for rel, _ in mine),
   '  and the census WALKED - projects/ is in it')

# ==========================================================================
head('2. NOT ONE OF THE TWENTY-FOUR STILL PAINTS THE COMPONENT')
# ==========================================================================
for rel, p in mine:
    left = more_rules(now(p))
    ok(not left, '%-38s declares no .action-more-* rule'
       % rel.replace('.html', ''), left[:3])
ok(all(more_rules(was(p)) for _, p in mine),
   '  CONTROL: every one of them did before this round')

# asset_detail is the proof that specificity, not order, was deciding.
ad = os.path.join(T, 'asset_detail.html')
ok(len(more_rules(was(ad))) >= 1 and len(was(ad)) - len(now(ad)) > 100,
   'asset_detail had a local copy at all', len(more_rules(was(ad))))
bc = css_of(now(BASE))
ok(any(bare(m.group(1)) == '.page-action-buttons .action-more-btn'
       for m in RULE.finditer(bc)),
   "  and base's button rule is SCOPED (0,2,0), which is why a bare "
   '(0,1,0) copy never applied however late it sat')

# ==========================================================================
head('3. base GAINS ONE LINE, AND SAYS AT LAST HOW THE MENU HIDES')
# ==========================================================================
bw = css_of(was(BASE))
ok(any(bare(m.group(1)) == '.action-more-menu[hidden]'
       for m in RULE.finditer(bc)),
   'base declares .action-more-menu[hidden]')
ok(not any(bare(m.group(1)) == '.action-more-menu[hidden]'
           for m in RULE.finditer(bw)),
   '  and did not before - every page that worked, worked on the '
   "BROWSER's own [hidden] rule")
body = [m.group(2) for m in RULE.finditer(bc)
        if bare(m.group(1)) == '.action-more-menu[hidden]']
ok(body and 'none' in body[0], '  and it hides it', body[0].strip()
   if body else '')
ok(len(css_of(now(BASE))) - len(css_of(was(BASE))) < 400,
   '  base gained nothing else of substance',
   '%d characters' % (len(css_of(now(BASE))) - len(css_of(was(BASE)))))

# ==========================================================================
head('4. THREE COLOURS OF ONE ICON, AND NOT ONE OF THEM MEANT ANYTHING')
# ==========================================================================
found = {}
for rel, p in mine:
    for m in RULE.finditer(css_of(was(p))):
        if bare(m.group(1)) == '.action-more-item i':
            c = re.search(r'(?:^|[;{])\s*color\s*:\s*([^;}]+)', m.group(2))
            found[rel] = c.group(1).strip() if c else '(none)'
tones = sorted({v for v in found.values() if v != '(none)'})
ok(len(tones) >= 3,
   'the same icon was written in %d different colours: %s'
   % (len(tones), ', '.join(tones)), found)
for rel, c in sorted(found.items()):
    print('        %-42s %s' % (rel, c))
ok(not any('var(' in c for c in found.values()),
   '  and not one of them was a token')
# None of those menus holds a destructive action, so none of the colours
# was carrying a meaning that is now lost.
for rel in found:
    mk = re.sub(r'<[^>]*>', ' ', was(os.path.join(T, *rel.split('/'))))
    ok('action-more-item-danger' not in was(os.path.join(T, *rel.split('/'))),
       '  %s holds no destructive item, so its colour meant nothing'
       % rel.replace('.html', ''))
ok(any(bare(m.group(1)) == '.action-more-item i' for m in RULE.finditer(bc)),
   '  base draws it, on a token, once for all of them')

# ==========================================================================
head('5. RENDERED - EVERY ONE OPENS, CLOSES, AND IS base\'S BOX')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

binder = [s for s in SCRIPT.findall(now(BASE)) if 'data-menu-toggle' in s]
boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = '\n'.join(styles_of(now(BASE)))


def fixture(page_text, strip=False):
    """base's stylesheet, the page's, and BOTH script sets.

    The page's own scripts are loaded as well as base's binder because
    three pages in this round still carry a hand-inlined handler - H8
    deferred them - and a fixture with only the binder reports their
    menus as broken when they are not. That mistake was made once, on
    invoices.html, before this was written this way."""
    cs = styles_of(page_text)
    if strip:
        cs = [strip_more(c) for c in cs]
    # ONE <script> PER SOURCE, NEVER ONE FOR ALL OF THEM. The first cut
    # of this concatenated every page script and base's binder into a
    # single element - and a page script that throws takes everything
    # after it in the SAME element down with it. Five pages reported a
    # menu 0px wide because their own code raised before the binder had
    # been reached. Separate elements are isolated: a throw ends that
    # element and the next one still runs, which is what the browser
    # does with the real page.
    parts = ['<script>%s</script>' % s for s in SCRIPT.findall(page_text)]
    if binder:
        parts.append('<script>%s</script>' % binder[0])
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div>%s</body></html>'
            % (boot, bcss, ''.join('<style>%s</style>' % c for c in cs),
               body_of(page_text), ''.join(parts)))


def strip_more(css):
    out, last = [], 0
    for m in RULE.finditer(css):
        if SEL.search(bare(m.group(1))):
            out.append(css[last:m.start()])
            last = m.end()
    out.append(css[last:])
    return ''.join(out)


STATE = """() => {
  const m = document.getElementById('actionMoreMenu');
  const b = document.getElementById('actionMoreBtn');
  if (!m || !b) return null;
  const rm = m.getBoundingClientRect(), rb = b.getBoundingClientRect();
  const si = getComputedStyle(document.querySelector('.action-more-item') ||
                              document.body);
  return {menuVis: rm.width > 0 && rm.height > 0,
          btnVis: rb.width > 0 && rb.height > 0,
          mw: Math.round(rm.width), bw: Math.round(rb.width),
          bh: Math.round(rb.height), itemColor: si.color};
}"""


def drive(pairs, width, strip, tag):
    from playwright.sync_api import sync_playwright
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': width, 'height': 700})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        for i, (rel, text) in enumerate(pairs):
            fx = os.path.join(SCRATCH, '%s_%d.html' % (tag, i))
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(text, strip))
            pg = ctx.new_page()
            _goto(pg, fx)
            s0 = pg.evaluate(STATE)
            if not s0 or not s0['btnVis']:
                out[rel] = ('no button', s0)
                pg.close()
                continue
            try:
                pg.click('#actionMoreBtn', timeout=4000)
            except Exception as e:
                out[rel] = ('click refused', str(e).split('\n')[0][:60])
                pg.close()
                continue
            s1 = pg.evaluate(STATE)
            pg.click('#actionMoreBtn', timeout=4000)
            s2 = pg.evaluate(STATE)
            out[rel] = ('driven', s0, s1, s2)
            pg.close()
        br.close()
    return out


if not HAVE or not binder:
    skip('the rendered probe', 'no browser, or no binder in base')
else:
    res = drive([(rel, now(p)) for rel, p in mine], 390, False, 'after')
    for rel, _ in mine:
        r = res[rel]
        if r[0] != 'driven':
            ok(False, '%-38s opens and closes' % rel.replace('.html', ''),
               '%s %s' % (r[0], r[1]))
            continue
        s0, s1, s2 = r[1], r[2], r[3]
        ok(not s0['menuVis'] and s1['menuVis'] and not s2['menuVis']
           and s1['mw'] == HOUSE_MENU_WIDTH,
           '%-38s closed - open (%dpx) - closed'
           % (rel.replace('.html', ''), s1['mw']),
           '%s / %s / %s' % (s0, s1, s2))
    widths = {res[rel][2]['mw'] for rel, _ in mine
              if res[rel][0] == 'driven'}
    ok(widths == {HOUSE_MENU_WIDTH},
       '  and all twenty-four are the SAME box now - %s' % sorted(widths),
       sorted(widths))

# ==========================================================================
head('6. THE TWO EXCLUSIONS, PROVED BY STRIPPING THEM IN THE FIXTURE')
# ==========================================================================
if not HAVE or not binder:
    skip('the rendered exclusions', 'no browser')
else:
    dash = os.path.join(T, 'property_management_dashboard.html')
    pl = os.path.join(T, 'finance_pl_act.html')
    for width, label in ((390, 'a phone'), (1280, 'a desktop')):
        keep = drive([('d', now(dash))], width, False, 'dash_k%d' % width)
        cut = drive([('d', now(dash))], width, True, 'dash_c%d' % width)
        k, c = keep['d'], cut['d']
        kb = '%dx%d' % (k[1]['bw'], k[1]['bh']) if k[0] != 'no button' \
            else 'no button'
        cb = '%dx%d' % (c[1]['bw'], c[1]['bh']) if c[0] != 'no button' \
            else 'GONE'
        ok(kb != cb,
           'property_management_dashboard on %-9s  keeps %s, stripped %s'
           % (label, kb, cb))
    # AS H9 LEFT IT, NOT AS IT IS NOW. H10 gave finance_pl_act the
    # `hidden` attribute and took its rules, so the live file no longer
    # renders open when they are stripped - and this check would report
    # that H9's exclusion was unjustified when it was justified at the
    # time. now() walks forward to the first later round's backup, which
    # is this page exactly as H9 left it. That is what alv_rounds is for,
    # and a suite asking about its OWN round must never read the live
    # file (lesson 40, from the other side again).
    strip_state = drive([('p', now(pl))], 390, True, 'pl_c')['p']
    keep_state = drive([('p', now(pl))], 390, False, 'pl_k')['p']
    ok(keep_state[0] == 'driven' and not keep_state[1]['menuVis'],
       'finance_pl_act arrives CLOSED with its own rules')
    ok(strip_state[0] == 'driven' and strip_state[1]['menuVis'],
       '  and arrives OPEN without them - which is why it is excluded',
       strip_state[1] if strip_state[0] == 'driven' else strip_state)

# ==========================================================================
head('7. CONTROLS, AND THE GATE')
# ==========================================================================
ok(SEL.search('.action-more-btn') is not None,
   'the selector pattern matches a More class')
ok(SEL.search('.action-more-btn-extra') is not None,
   '  and a longer one that starts the same way, deliberately - the '
   'patcher refuses a MIXED list rather than guessing')
ok(SEL.search('.action-primary') is None,
   '  and does not match a bar button')
ok(not more_rules('<style>/* .action-more-item */ a{x:1}</style>'),
   '  and is not tripped by a class named inside a CSS comment')
ok(len(strip_more('.a{x:1}.action-more-item{y:2}.b{z:3}')) ==
   len('.a{x:1}.b{z:3}'),
   '  the fixture stripper removes only the rule it is aiming at')

ok(more_rules(was(os.path.join(T, 'view_recipe.html'))),
   'reverting a page puts its copy back, so section 2 would FAIL')
ok('.action-more-menu[hidden]' not in css_of(was(BASE)),
   '  and reverting base takes the hide rule with it, so section 3 would '
   'FAIL too')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_subtree' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_subtree'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  WHAT THIS UNBLOCKS. H8 left base\'s menu binder OPT-IN, because')
print('  three pages still carry a hand-inlined handler and a class-wide')
print('  binder would double-bind them. Two of those three - invoices and')
print('  physical_invoice_list - have now given up their CSS as well, so')
print('  only their handlers remain. When those go, the binder can bind')
print('  .action-more-wrapper directly and the three attributes stop')
print('  being needed at all.')
print('=' * 74)
sys.exit(1 if failed else 0)
