# -*- coding: utf-8 -*-
"""test_crs_hub.py - Section X round X5, 28 Sep 2026.

Demetri, on the CRS screens: "This should not be green. Help button
should not be green. The table should not have a green border. The view
modal should comply to our standards."

X0 made the module visible without changing a pixel. X1 changes them, on
ONE screen, all the way through - so the finished shape can be looked at
before it is repeated for Reporting FIs and Submissions.

SECTION 1 IS THE PANEL, AND WHY THIS ROUND KEEPS WHAT FOUR ROUNDS
DELETED. X1 to X4 removed .crs-panel from the list and form screens
because a house list or form page has no outer panel. A HUB does -
personal.html's is 30px of padding, a 3px solid border and a radius,
coloured from --alv-accent and --alv-accent-soft, which is the CRS
panel's shape to the pixel. So here the answer really is a retone, and
the rule that decided it both ways is the same: look at what the house
does for THIS KIND OF PAGE.

SECTION 2 IS THE TILES AND THE HELP BUTTON.

SECTION 3 IS THE TWO DEAD RULES, proved unworn before they were deleted.

SECTION 4 RENDERS IT, before and after, at 1280 and 390, against the
house hub.

SECTION 5 IS WHAT THE ROUND FOUND AND DID NOT FIX.
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

import alv_tree

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

SUFFIX = '.bak_crshub'
ME = 'test_crs_hub.py'
PATCHER = 'apply_crs_hub.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = os.path.join(ROOT, 'crs', 'templates', 'crs', 'index.html')
BASE = os.path.join(T, 'base.html')
HOUSE = os.path.join(T, 'suppliers.html')   # the control: a house list page
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

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
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def bare(s):
    """Lesson 21 - strip CSS comments before ANY selector comparison."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def nocmt(s):
    """The same, for a body or a whole file. X1's own patcher failed its
    first hex gate on the explanatory comment it had just written."""
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def sels(css):
    return [bare(m.group(1)) for m in RULE.finditer(css)]


def markup(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)


def has_class(mk, name):
    """A whole class token, not a substring. `action-icon` is inside
    `mobile-action-icon`, and the patcher's first gate fell for it."""
    return bool(re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', mk))


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


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
    return re.sub(r'\{\{.*?\}\}', 'AT', b, flags=re.S)


pn, pw_ = now(PAGE), was(PAGE)
cn = '\n'.join(STYLE.findall(pn))
cw = '\n'.join(STYLE.findall(pw_))
mn, mw = markup(pn), markup(pw_)
HOUSE = os.path.join(T, 'personal.html')
hc = '\n'.join(STYLE.findall(read(HOUSE)))


def rule(css, sel):
    return [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]


def decl(body_, prop):
    m = re.search(r'(?:^|[;{])\s*' + prop + r'\s*:\s*([^;}]+)', body_)
    return ' '.join(m.group(1).split()) if m else None


print('=' * 74)
print('%s - X5, THE CRS HUB' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE PANEL IS KEPT - AND FOUR ROUNDS DELETED ONE')
# ==========================================================================
ok('--crs-dark' in cw, 'CONTROL: the hub declared the module palette')
was_p = rule(cw, '.crs-panel')
ok(was_p and 'var(--crs-dark)' in was_p[0],
   '  and painted its panel from it', was_p)

house_p = rule(hc, '.tab-panel')
ok(house_p, 'personal.html - the house hub - HAS a panel', house_p)
ok(house_p and decl(house_p[0], 'padding') == '30px'
   and decl(house_p[0], 'border') == '3px solid',
   '  30px of padding and a 3px solid border', house_p)
now_p = rule(cn, '.crs-panel')
ok(now_p and decl(now_p[0], 'padding') == '30px'
   and decl(now_p[0], 'border') == '3px solid var(--alv-accent)',
   '  and the CRS panel is that shape to the pixel - only the colour was '
   'ever wrong', now_p)
ok(now_p and 'var(--alv-accent-soft)' in now_p[0],
   '  it now takes the accent pair, as personal.html does')
hp = rule(hc, '.tab-panel.personal-panel')
ok(hp and 'var(--personal-dark)' in hp[0],
   '  CONTROL: which personal.html reaches through a local alias onto '
   '--alv-accent; this page uses the token directly', hp)

# THE DISTINCTION, MADE EXECUTABLE.
for page, want in (('country_list.html', False), ('fi_list.html', False),
                   ('country_form.html', False), ('fi_form.html', False),
                   ('index.html', True)):
    p = os.path.join(ROOT, 'crs', 'templates', 'crs', page)
    got = bool(rule('\n'.join(STYLE.findall(read(p))), '.crs-panel'))
    ok(got is want,
       '  %-22s %s a panel' % (page, 'keeps' if want else 'has no'))

ok('--crs-' not in nocmt(pn), 'no --crs-* token has a reader any more',
   re.findall(r'--crs-\w+', nocmt(pn))[:4])
ok(not re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cn)),
   '  and the page stylesheet carries no hex',
   sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cn)))))

# ==========================================================================
head('2. THE TILES AND THE HELP BUTTON')
# ==========================================================================
was_t = rule(cw, '.crs-btn')
ok(was_t and '#28a745' in was_t[0],
   'CONTROL: the three tiles were painted with a Bootstrap green hex',
   decl(was_t[0], 'background-color') if was_t else '')
now_t = rule(cn, '.crs-btn')
ok(now_t and decl(now_t[0], 'background-color') == 'var(--alv-accent)',
   '  and now take the house accent',
   decl(now_t[0], 'background-color') if now_t else '')
hb = rule(hc, '.btn-personal')
ok(hb and decl(hb[0], 'background-color') == 'var(--alv-accent)',
   '  CONTROL: which is exactly what personal.html\'s tiles use', hb)
hov = rule(cn, '.crs-btn:not(.coming-soon):hover')
ok(hov and 'var(--alv-accent-ink)' in hov[0],
   '  and the hover follows onto --alv-accent-ink, as the house hover does',
   hov)
ok(mn.count('crs-btn') == 3, '  three tiles', mn.count('crs-btn'))

ok('action-icon' in mw,
   'CONTROL: Help carried `action-icon`, a class base has never owned')
ok(not has_class(mn, 'action-icon') and not has_class(mn, 'btn-success'),
   'neither survives')
ok('btn action-secondary' in mn, '  and Help is the house Help button')
ok('ALIVENTE ONLINE -' in mw and 'ALIVENTE ONLINE -' not in mn,
   'the title drops the brand prefix')
for h6 in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mn, re.S):
    ok('<center>' not in h6, '  and no heading wraps itself in <center>',
       ' '.join(h6.split())[:60])

# ==========================================================================
head('3. THE TWO DEAD RULES, PROVED UNWORN BEFORE DELETION')
# ==========================================================================
ok('.crs-btn.coming-soon' in [bare(m.group(1)) for m in RULE.finditer(cw)],
   'CONTROL: the page carried .crs-btn.coming-soon')
ok('.crs-coming-label' in [bare(m.group(1)) for m in RULE.finditer(cw)],
   '  and .crs-coming-label')
ok(not has_class(mw, 'coming-soon') and not has_class(mw, 'crs-coming-label'),
   '  and NOTHING in the markup wore either, before the round or after - '
   'they are left over from when all three tiles were placeholders')
ok('.crs-btn.coming-soon' not in [bare(m.group(1))
                                  for m in RULE.finditer(cn)],
   'both are gone')
ok('.crs-coming-label' not in [bare(m.group(1)) for m in RULE.finditer(cn)],
   '  and so is the label rule')
ok(':not(.coming-soon)' in ' '.join(bare(m.group(1))
                                    for m in RULE.finditer(cn)),
   '  the hover selector still NAMES coming-soon, and is left alone: it '
   'is a :not() that matches everything now, and rewriting it would be a '
   'change this round did not measure')

# ==========================================================================
head('4. RENDERED, BEFORE AND AFTER, AGAINST THE HOUSE HUB')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

boot = read(BOOT) if os.path.isfile(BOOT) else ''
base_t = read(BASE)


def fixture(page_text):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div></body></html>'
            % (boot, '\n'.join(styles_of(base_t)),
               ''.join('<style>%s</style>' % c for c in styles_of(page_text)),
               body_of(page_text)))


PROBE = """() => {
  const g = (el, p) => el ? getComputedStyle(el)[p] : null;
  const panel = document.querySelector('.crs-panel, .tab-panel');
  const tile = document.querySelector('.crs-btn, .admin-btn');
  const help = [...document.querySelectorAll('button,a')].find(
      e => (e.getAttribute('aria-label')||'') === 'Help');
  return {
    panel_bw: g(panel, 'borderTopWidth'),
    panel_bc: g(panel, 'borderTopColor'),
    panel_bg: g(panel, 'backgroundColor'),
    panel_pad: g(panel, 'paddingTop'),
    tile_bg: g(tile, 'backgroundColor'),
    help_bg: g(help, 'backgroundColor'),
    tiles: document.querySelectorAll('.crs-btn').length,
  };
}"""

GREEN = 'rgb(40, 167, 69)'
PALE_GREEN = 'rgb(212, 237, 218)'


def measure(text_, width, tag):
    from playwright.sync_api import sync_playwright
    fx = os.path.join(SCRATCH, '%s_%d.html' % (tag, width))
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(fixture(text_))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': width, 'height': 1000})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        out = pg.evaluate(PROBE)
        br.close()
    return out


if not HAVE:
    skip('the rendered probe', 'playwright is not installed')
else:
    for width in (1280, 390):
        b = measure(pw_, width, 'before')
        a = measure(pn, width, 'after')
        print('  -- %dpx' % width)
        ok(b['panel_bc'] == GREEN and b['panel_bg'] == PALE_GREEN,
           '  CONTROL: the panel was green on pale green', b)
        ok(a['panel_bc'] != GREEN and a['panel_bg'] != PALE_GREEN,
           '  and is now %s on %s' % (a['panel_bc'], a['panel_bg']))
        ok(a['panel_bw'] == b['panel_bw'] and a['panel_pad'] == b['panel_pad'],
           '  and its SHAPE did not move - same border width, same padding',
           {'before': [b['panel_bw'], b['panel_pad']],
            'after': [a['panel_bw'], a['panel_pad']]})
        ok(b['tile_bg'] == GREEN, '  CONTROL: the tiles were green',
           b['tile_bg'])
        ok(a['tile_bg'] != GREEN, '  and are now %s' % a['tile_bg'])
        ok(b['help_bg'] == GREEN, '  CONTROL: Help was green', b['help_bg'])
        ok(a['help_bg'] != GREEN, '  and is not (%s)' % a['help_bg'])
        ok(a['tiles'] == 3, '  three tiles, still', a['tiles'])

    h = measure(read(HOUSE), 1280, 'house')
    a = measure(pn, 1280, 'after')
    ok(h['panel_bw'] == a['panel_bw'] and h['panel_pad'] == a['panel_pad'],
       'CONTROL: the CRS panel and the house hub panel are the same shape',
       {'personal': [h['panel_bw'], h['panel_pad']],
        'crs': [a['panel_bw'], a['panel_pad']]})
    ok(h['tile_bg'] == a['tile_bg'],
       '  and the tiles are now the same colour',
       {'personal': h['tile_bg'], 'crs': a['tile_bg']})

# ==========================================================================
head('5. FOUND, NOT FIXED')
# ==========================================================================
copies = []
for p in alv_tree.templates():
    c = '\n'.join(STYLE.findall(read(p)))
    for sel in ('.admin-btn', '.crs-btn'):
        if rule(c, sel):
            copies.append('%s: %s' % (alv_tree.rel(p), sel))
            break
ok(len(copies) == 3,
   'the hub TILE component is defined %d times, under two names for the '
   'same thing, and base owns none of it' % len(copies), copies)
print('')
print('     That is the shape the More-menu rounds had before H8 and H9')
print('     hoisted them. It wants the same treatment, as a round of its')
print('     own - it touches pages nobody reported, and folding it into a')
print('     one-page colour fix would have hidden it.')
print('')
ok(mn.count('<center>') == 1,
   'the message block keeps its <center> - that is the message-bar round')

# ASSERTED AGAINST A REGISTER, NOT A NUMBER.
green = [n for n in alv_tree.crs_pages()
         if '--crs-dark' in nocmt(read(os.path.join(
             ROOT, 'crs', 'templates', n)))]
ok(sorted(green) == sorted(alv_tree.crs_outstanding()),
   'exactly the CRS pages that have NOT had their round still carry the '
   'local palette - %d of %d' % (len(green), len(alv_tree.crs_pages())),
   {'still green': green, 'expected': alv_tree.crs_outstanding()})
print('')
print('  CRS PAGES STILL TO DO - %d:' % len(alv_tree.crs_outstanding()))
for n in alv_tree.crs_outstanding():
    print('     %s' % n)

# ==========================================================================
head('6. CONTROLS, AND THE GATE')
# ==========================================================================
ok(bare('/* banner */ .crs-btn') == '.crs-btn',
   'the selector reader strips a comment banner (lesson 21)')
ok(has_class('class="mobile-action-icon"', 'mobile-action-icon')
   and not has_class('class="mobile-action-icon"', 'action-icon'),
   '  and a class test does not fire on a longer name containing it')
ok('--crs-dark' in nocmt(pw_),
   'reverting the page brings the palette back, so section 1 would FAIL - '
   'a revert is caught')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_crsfiform' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_crsfiform'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(os.path.join(ROOT, PS1)) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NEXT: Submissions - three screens, and the last of the module.')
print('  submission_detail.html alone is 49KB with 28 hexes and nine')
print('  Bootstrap colour buttons.')
print('=' * 74)
sys.exit(1 if failed else 0)
