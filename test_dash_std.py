# -*- coding: utf-8 -*-
"""test_dash_std.py - DB-5, THE PROPERTY DASHBOARD ONTO HOUSE STANDARDS

Sections 1 to 4 read the file. Sections 5 to 8 RENDER it, in a real
browser, and section 7 READS PIXELS - which is the only way to measure
what this round actually fixed.

WHY PIXELS. The page dimmed four times with `opacity`, and neither
test_pair_contrast.py nor test_contrast.py contains the word `opacity`:
every contrast gate in this system reads DECLARED COLOUR PAIRS, so all
four dims passed every sweep since the page was written. A gate that
reads what the CSS says cannot see what the screen shows. So this suite
screenshots the label and asks the image.

That is also why section 7 is the only place in the programme using
PIL. It is not a new dependency for its own sake; it is the instrument
the finding needed.

SECTION 6 IS THE HEADLINE. Before this round the Property Dashboard
could not be used from a keyboard at all - the selector, all twelve
tiles and every row in the picker were plain divs with a click listener
and no role, no tabindex and no key handler. Section 6 counts
keyboard-reachable controls in the rendered page, before and after, and
the number it reports for the twelve tiles BEFORE is zero.

AND IT REPORTS ZERO AFTER TOO, until a property is chosen. That is the
right answer, not a failure: the tiles are anchors whose href the script
fills in on selection, so the absence of an href is what holds them
shut. Section 6 drives the real selection handler and counts again.

WHAT IS NOT PROVED HERE: that any of the twelve destinations is right -
the URLs moved from a click handler to a function unchanged and this
round did not touch routing. Nor that `0.75` is the dim Demetri will
want; it is the LOWEST dim at which the accent icon clears 3.0:1, which
is a floor and not a preference.
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

SUFFIX = '.bak_dashstd'
ME = 'test_dash_std.py'
PATCHER = 'apply_dash_std.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'property_management_dashboard.html'
REFERENCE = 'properties.html'
BASE = alv_tree.join('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

TILES = 12
TWINS = 12
SIDE_RULES = 10
RULES_WAS, RULES_NOW = 52, 26

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
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    """The page as this round found it. A suite that judges a round
    against what it replaced cannot run without the backup, and saying
    so beats 40 confusing failures."""
    b = p + SUFFIX
    if not os.path.isfile(b):
        print('')
        print('  !! %s has no %s backup.' % (os.path.basename(p), SUFFIX))
        print('     This suite measures the round against what it')
        print('     replaced, so it cannot run until %s has.' % PATCHER)
        sys.exit(1)
    return read(b)


def now(p):
    return read(p)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def bare(s):
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


# THE HOUSE STRIPPER, ALIASED - NOT A SIXTH PRIVATE COPY.
#
# The first draft of this round DEFINED code_only here and again in its
# suite, and test_code_only.py refused both: "no other file in the tree
# defines code_only". That suite exists precisely to stop this. 45 files
# alias it - 22 patchers and 23 suites - and 47 defined it before CO-1
# hoisted it on 3 Oct.
#
# Wrapping it in a def of my own was the SECOND wrong answer: a function
# that calls the house one is still a definition, and the suite counts
# definitions. The house pattern is an assignment.
#
# And the copy I wrote was worse than the one already on the shelf. Mine
# blanked every /* ... */ in the file; the house one does that only
# inside <style> and <script>, because `/*` IS NOT A COMMENT OPENER IN
# MARKUP - accept="image/*" puts one inside an attribute value, and
# blanking from there costs 94 lines of the Add Passport form. That is
# measured, written down, and three weeks old.
#
# code_only, NOT code_only_js. The _js variant also strips // line
# comments inside a <script>, and test_code_only pins it to "exactly the
# three suites that need it" - taking it would have made that four for
# no reason. Measured both against all seventeen counts below: identical
# answers, because nothing this round counts hides behind a // comment.
# Take what you need, not what is nearest.
#
# A GATE READS CODE, NOT THE RECORD OF CODE. The sixth time round, the
# answer was already in alv_tree and the only new thing was my not
# looking.
code_only = alv_tree.code_only


def rules_of(t):
    out = []
    for m in STYLE.finditer(t):
        for s in re.finditer(r'(?m)^\s*([.#][^\n{}]*?)\s*\{', m.group(1)):
            out.append(s.group(1).strip())
    return out


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
    return re.sub(r'\{\{.*?\}\}', '42', b, flags=re.S)


P = alv_tree.join(PAGE)
SRC, OLD = now(P), was(P)
CODE, OLDCODE = code_only(SRC), code_only(OLD)

print('=' * 74)
print('%s - DB-5, THE PROPERTY DASHBOARD ONTO HOUSE STANDARDS' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE ROUND IS ON DISK, REGISTERED, AND IN THE RIGHT ORDER')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-4:] if ROUNDS else 'ROUNDS empty')
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(PAGE not in str(alv_tree.WAITING), '  and this page is not on WAITING')

# THE ORDER IS THE REAL PROPERTY, NOT RECENCY. Every earlier suite that
# reads this page does so through as_left_by, which walks ROUNDS FORWARD
# from its own suffix to the first later backup that exists. Registered
# last, DB-5's backup is what they now find - so they keep reading the
# page as their own round left it. Registered anywhere else, three
# suites start measuring a file they were never written against.
for earlier in ('.bak_linesoft', '.bak_accentink', '.bak_morecss',
                '.bak_lastmenu', '.bak_pileases'):
    ok(earlier in ROUNDS and ROUNDS.index(earlier) < ROUNDS.index(SUFFIX),
       '  registered AFTER %s' % earlier)

# ==========================================================================
head('2. THE ACTION BAR - THE SHAPE %s HAS' % REFERENCE.upper())
# ==========================================================================
ok('class="page-action-buttons"' in CODE,
   'the page has a .page-action-buttons bar')
ok('class="page-action-buttons"' not in OLDCODE,
   '  CONTROL: and it had none before - of 33 pages carrying an '
   'action-more-wrapper, this was the one of 33 outside a bar')

ok(CODE.count('id="choosePropertyBtn"') == 1
   and 'btn action-primary" id="choosePropertyBtn"' in CODE,
   'Choose Property is a real .action-primary button')
ok(CODE.count('btn action-secondary') == 1
   and 'data-target="#dashboardHelpModal"' in CODE,
   '  Help is a desktop secondary, which is what base shows at '
   'desktop width')
ok(CODE.count('class="action-more-item"') == 1,
   '  and the same Help is the one item in the phone More menu')
ok('<span class="action-back-label"> Back</span>' in CODE,
   '  Back carries the house label, hidden below 768px by base')

for gone, what in (('dashboard-side-actions', 'the 56px side column'),
                   ('action-back-stacked', 'its hand-made Back geometry'),
                   ('property-selector-card', 'the teal slab'),
                   ('selector-label', 'the slab label'),
                   ('selector-hint', 'the slab hint'),
                   ('dashboard-top-row', 'the two-column shell')):
    ok(gone not in CODE, '  %s is gone - %s' % (gone, what))
    ok(gone in OLDCODE, '    CONTROL: and it really was there before')

sw = [r for r in rules_of(OLD) if 'dashboard-side-actions' in r]
ok(len(sw) == SIDE_RULES,
   '  it took %d .dashboard-side-actions rules with it - eight in the '
   'desktop block and two more in the mobile one' % SIDE_RULES, len(sw))
ok(not [r for r in rules_of(SRC) if 'dashboard-side-actions' in r],
   '    and not one survives')
ok(len(rules_of(OLD)) == RULES_WAS and len(rules_of(SRC)) == RULES_NOW,
   '  the page own CSS: %d rules -> %d' % (RULES_WAS, RULES_NOW),
   '%d -> %d' % (len(rules_of(OLD)), len(rules_of(SRC))))

ok('class="alv-card alv-chosen-property"' in CODE
   and 'class="alv-card-head"' in CODE and 'class="alv-card-body"' in CODE,
   'the chosen property sits on base .alv-card / -head / -body')
ok(CODE.count('form-section-title') == 3
   and 'class="section-title"' not in CODE,
   '  and the three section headings are base .form-section-title')
ok('class="section-title"' in OLDCODE,
   '    CONTROL: they were a private copy before')
ok('container-fluid' not in CODE and '<div class="container">' in CODE,
   '  the page is on plain .container, like 96 of 151')

# ==========================================================================
head('3. ONE LINE IN base EXPLAINS THE WHOLE SIDE COLUMN')
# ==========================================================================
bcss_raw = '\n'.join(styles_of(now(BASE)))


def outside_media(css, needle):
    i = css.find(needle)
    if i < 0:
        return False
    for m in re.finditer(r'@media[^{]*\{', css[:i]):
        depth, j = 1, m.end()
        while j < i and depth:
            depth += 1 if css[j] == '{' else (-1 if css[j] == '}' else 0)
            j += 1
        if depth:
            return False
    return True


HIDE = '.action-more-wrapper { display: none; }'
BTN = '.page-action-buttons .action-more-btn {'
ok(outside_media(bcss_raw, HIDE),
   'base hides .action-more-wrapper OUTSIDE any media query')
ok(BTN in bcss_raw and not outside_media(bcss_raw, BTN),
   '  and styles the button, the menu and the items only INSIDE one')
print('        SO BASE\'S MORE MENU IS A PHONE COMPONENT. At desktop')
print('        width the wrapper is hidden and the .action-secondary')
print('        buttons show; below 768px the secondaries hide and the')
print('        menu takes over. The dashboard was the only page in the')
print('        app with a local rule naming .action-more-wrapper, and')
print('        the only More button visible on a desktop - at (0,2,0),')
print('        beating base\'s (0,1,0).')
ok('.dashboard-side-actions .action-more-wrapper' in bare(OLD),
   '  CONTROL: and that override really was the page\'s own rule')

# .form-section-title is not merely "the house one" - it is the SAME
# declarations. A migration onto a component that renders differently
# is a repaint wearing a migration's clothes.
want = {'color': 'var(--alv-ink)', 'font-weight': '600',
        'border-bottom': '2px solid var(--alv-accent)'}
fst = {}
for m in RULE.finditer(bcss_raw):
    if bare(m.group(1)) == '.form-section-title':
        for d in m.group(2).split(';'):
            if ':' in d:
                k, v = d.split(':', 1)
                fst[k.strip()] = ' '.join(v.split())
miss = {k: (v, fst.get(k)) for k, v in want.items() if fst.get(k) != v}
ok(not miss,
   '  base .form-section-title declares the same ink, weight and accent '
   'underline the private copy did', miss)
oldsec = {}
for m in RULE.finditer('\n'.join(styles_of(OLD))):
    if bare(m.group(1)) == '.section-title':
        for d in m.group(2).split(';'):
            if ':' in d:
                k, v = d.split(':', 1)
                oldsec[k.strip()] = ' '.join(v.split())
ok(all(oldsec.get(k) == v for k, v in want.items()),
   '    CONTROL: and the copy it replaced declared them identically - '
   'a migration, not a repaint', oldsec)

# ==========================================================================
head('4. THE TOKENS, THE LINKS, AND THE RECORD THAT HAD TO SURVIVE')
# ==========================================================================
ok('border-radius: 10px' not in CODE
   and CODE.count('var(--alv-radius-sm)') == 1,
   'the tile radius is the house token, not a 10px literal')
ok('border-radius: 10px' in OLDCODE, '  CONTROL: it was 10px before')
for lit in ('border-radius: 12px', 'border-radius: 8px'):
    ok(lit not in CODE, '  %s is gone with the rule that held it' % lit)
ok('#adb5bd' not in CODE, 'no hex literal survives in the page CSS')
ok(OLDCODE.count('#adb5bd') == 3,
   '  CONTROL: three did before - 35 RGB units off --alv-ink-faint, '
   'which is above B-2b\'s 25-unit bound, so the colour rounds were '
   'right to leave them')
ok(CODE.count('var(--alv-ink-soft)') == 2
   and CODE.count('var(--alv-ink-faint)') == 1,
   '  two switched-off tile rules on --alv-ink-soft, the chevron on '
   '--alv-ink-faint')

ok(CODE.count('<a class="dash-card" data-box-type="') == TILES,
   'all %d live tiles are real <a> elements' % TILES)
ok(OLDCODE.count('<div class="dash-card" data-box-type="') == TILES,
   '  CONTROL: all %d were plain divs before' % TILES)
ok(CODE.count('<div class="dash-card dash-card-disabled"') == TWINS
   and '<a class="dash-card dash-card-disabled"' not in CODE,
   'and all %d permission-denied twins stay divs - they are not links'
   % TWINS)
print('        A replace on class="dash-card" alone would have taken all')
print('        24, and the result renders identically. It would only be')
print('        wrong for the users who have no permission, which is the')
print('        set least likely to be the one testing it.')
ok('href=' not in re.sub(r'\{%.*?%\}', '', CODE.split('dashboard-grids')[1]
                         .split('propertyPickerModal')[0]),
   'no tile carries an href in the MARKUP - it cannot, because the '
   'property id is not known at render time')
ok(CODE.count("setAttribute('href'") == 1,
   '  and exactly one place in the script gives a tile a destination')
ok('clicked' not in CODE,
   '  .dash-card.clicked and its timers are gone - a link navigates, '
   'and the browser\'s own feedback is the feedback')
ok(OLDCODE.count('clicked') >= 3,
   '    CONTROL: the rule and both timers were there before',
   OLDCODE.count('clicked'))
ok('pointer-events: none' not in bare(
       '\n'.join(styles_of(SRC))).split('.dash-card.dash-card-disabled')[0],
   'the GRID is no longer locked with pointer-events')
print('        THE ABSENCE OF AN HREF IS THE LOCK. An <a> with no href')
print('        is neither focusable nor clickable, which a keyboard')
print('        respects and pointer-events never did. That is why the')
print('        dim could come up from .45 to .75: it stopped being the')
print('        lock and became the signal.')
ok('pointer-events: none' in CODE,
   '  CONTROL: the TWIN keeps its pointer-events - that one is not an '
   'anchor and has nothing else holding it shut')

# THE OTHER HALF OF code_only. Every count above was taken from the
# comment-stripped text; the explanation has to survive in the raw file
# or the next reader inherits a page with no history.
for word in ('dashboard-side-actions', 'Click to choose', '#adb5bd',
             'container-fluid', 'property-selector-card',
             '.dash-card.clicked'):
    ok(word in SRC,
       '  the record of %r survived in a comment' % word)

# ==========================================================================
head('5. THE FIXTURE - base, bootstrap, the page, and a twin on purpose')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

try:
    from PIL import Image
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = '\n'.join(styles_of(now(BASE)))
binder = [s for s in SCRIPT.findall(now(BASE)) if 'data-menu-toggle' in s]

# A jQuery STUB, not jQuery. The page calls
# $('#propertyPickerModal').modal('show'|'hide') and nothing else, so a
# stub lets the page's OWN selectProperty run - which is what section 6
# has to drive. Loading real jQuery would add a second thing that can
# fail and prove nothing extra.
JQ = ("window.$ = window.jQuery = function(){ return { modal: "
      "function(){ return this; } }; };")

# ONE TWIN, DELIBERATELY. one_branch() resolves every {% if %} to its
# first branch, so the fixture renders twelve LIVE tiles and no
# permission-denied twin at all - and section 7's whole subject is the
# twin. The Properties round learned this the hard way: its grey check
# measured nothing, because the else-branch class never reached the DOM.
TWIN = ('<div class="dashboard-section"><div class="dashboard-grid">'
        '<div class="dash-card dash-card-disabled" id="probeTwin" '
        'title="You do not have permission to access Properties">'
        '<div class="dash-card-icon"><i class="fas fa-chart-line"></i></div>'
        '<div class="dash-card-label">Property Report</div>'
        '</div></div></div>')


def fixture(page_text, twin=True):
    cs = styles_of(page_text)
    body = body_of(page_text)
    if twin:
        body += TWIN
    parts = ['<script>%s</script>' % JQ]
    parts += ['<script>%s</script>' % s for s in SCRIPT.findall(page_text)]
    if binder:
        parts.append('<script>%s</script>' % binder[0])
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s'
            '<style>body{background:#fff}</style></head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div>%s</body></html>'
            % (boot, bcss, ''.join('<style>%s</style>' % c for c in cs),
               body, ''.join(parts)))


FOCUS = """() => {
  const sel = 'a[href], button:not([disabled]), input, select, textarea,' +
              '[tabindex]:not([tabindex="-1"])';
  const vis = e => {
    const r = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden';
  };
  const all = Array.from(document.querySelectorAll(sel));
  const tiles = Array.from(document.querySelectorAll('.dash-card'))
      .filter(e => e.matches(sel));
  const rows = Array.from(document.querySelectorAll('.property-picker-item'))
      .filter(e => e.matches(sel));
  const chooser = Array.from(document.querySelectorAll(
      '#choosePropertyBtn, #propertySelectorCard')).filter(e => e.matches(sel));
  return {total: all.length, visible: all.filter(vis).length,
          tiles: tiles.length, rows: rows.length,
          chooser: chooser.length,
          hrefs: Array.from(document.querySelectorAll('.dash-card[href]'))
                      .length};
}"""

BAR = """() => {
  const bar = document.querySelector('.page-action-buttons');
  if (!bar) return null;
  const kind = e =>
      e.classList.contains('action-primary') ? 'primary' :
      e.classList.contains('action-secondary') ? 'secondary' :
      e.classList.contains('action-more-wrapper') ? 'more' :
      e.classList.contains('action-back') ? 'back' : 'other';
  return Array.from(bar.children).map(e => {
    const r = e.getBoundingClientRect();
    return {kind: kind(e), w: Math.round(r.width), h: Math.round(r.height),
            vis: r.width > 0 && r.height > 0,
            txt: (e.textContent || '').trim().slice(0, 20)};
  });
}"""

BOX = """(sel) => {
  const e = document.querySelector(sel);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return {x: r.x, y: r.y, w: r.width, h: r.height};
}"""

# WHY THE ICON IS NOT READ FROM PIXELS.
#
# Font Awesome is a webfont, and this fixture aborts every http request
# on purpose - a gate that passes only when a CDN is up is not a gate.
# With no glyph the icon div has no content, and `.dash-card` is a
# centred flex column, so it collapses to ZERO WIDTH: there is nothing
# on screen to screenshot. On the real page the glyph renders and the
# box is 32px.
#
# So for the icon the browser is asked for the RESOLVED cascade instead
# - the computed colour, and the product of the `opacity` of the element
# and every ancestor - and the composite is done here. That is still a
# measurement of the real cascade and not of the declaration, which is
# the thing no other gate in this system does. It is simply not a
# photograph, and this suite says so rather than quietly reporting a
# ratio of 1.00 for an invisible box.
COMPOSITE = """(sel) => {
  const e = document.querySelector(sel);
  if (!e) return null;
  const px = s => { const m = s.match(/[\d.]+/g); return m ?
      m.slice(0, 3).map(Number) : null; };
  let a = 1, n = e;
  while (n && n.nodeType === 1) {
    const o = parseFloat(getComputedStyle(n).opacity);
    if (!isNaN(o)) a *= o;
    n = n.parentElement;
  }
  const fg = px(getComputedStyle(e).color);
  let bg = null, q = e;
  while (q && q.nodeType === 1 && !bg) {
    const c = getComputedStyle(q).backgroundColor;
    const m = c.match(/[\d.]+/g);
    if (m && (m.length < 4 || Number(m[3]) > 0)) bg = m.slice(0, 3).map(Number);
    q = q.parentElement;
  }
  return {fg: fg, bg: bg || [255, 255, 255], alpha: a};
}"""


def srgb(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum(rgb):
    r, g, b = rgb[:3]
    return 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def measure(png):
    """The contrast a human sees in this box, read off the image.

    Background is the commonest pixel; foreground is the pixel furthest
    from it in luminance. Antialiasing means the extreme pixel is close
    to, and never darker than, the true ink - so this UNDERSTATES a bad
    ratio rather than inventing a good one.
    """
    im = Image.open(png).convert('RGB')
    # getdata() is deprecated from Pillow 14 and the replacement does
    # not exist before it. A gate that prints a DeprecationWarning is
    # a gate that trains people to ignore its output.
    px = list(im.get_flattened_data() if hasattr(im, 'get_flattened_data')
              else im.getdata())
    if not px:
        return None
    counts = {}
    for p in px:
        counts[p] = counts.get(p, 0) + 1
    bg = max(counts, key=counts.get)
    fg = max(px, key=lambda p: abs(lum(p) - lum(bg)))
    return (round(ratio(fg, bg), 2), '#%02x%02x%02x' % fg,
            '#%02x%02x%02x' % bg)


def probe(text, width, tag, twin=True, choose=False):
    """Render, optionally drive the real selection handler, and report."""
    from playwright.sync_api import sync_playwright
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': width, 'height': 1400})
        # HERMETIC. Nothing in a suite may reach the network: a gate that
        # passes only when a CDN is up is not a gate.
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        fx = os.path.join(SCRATCH, '%s.html' % tag)
        with open(fx, 'w', encoding='utf-8') as fh:
            fh.write(fixture(text, twin))
        pg = ctx.new_page()
        _goto(pg, fx)
        if choose:
            # THE PAGE'S OWN HANDLER, not a reimplementation of it.
            # .click() on the element fires the listener whether or not
            # Bootstrap would have shown the modal.
            pg.evaluate("() => { const r = document.querySelector("
                        "'.property-picker-item'); if (r) r.click(); }")
        out['focus'] = pg.evaluate(FOCUS)
        out['bar'] = pg.evaluate(BAR)
        out['shots'] = {}
        if HAVE_PIL:
            for name, sel in (('tile_label', '.dash-card-label'),
                              ('twin_label', '#probeTwin .dash-card-label')):
                b = pg.evaluate(BOX, sel)
                if not b or b['w'] < 2 or b['h'] < 2:
                    continue
                f = os.path.join(SCRATCH, '%s_%s.png' % (tag, name))
                pg.screenshot(path=f, clip={'x': b['x'], 'y': b['y'],
                                            'width': b['w'],
                                            'height': b['h']})
                out['shots'][name] = measure(f)
        out['cascade'] = {}
        for name, sel in (('tile_icon', '.dash-card-icon'),
                          ('tile_label', '.dash-card-label')):
            c = pg.evaluate(COMPOSITE, sel)
            if c and c['fg'] and c['bg']:
                eff = [c['fg'][i] * c['alpha'] + c['bg'][i] * (1 - c['alpha'])
                       for i in range(3)]
                out['cascade'][name] = (
                    round(ratio(eff, c['bg']), 2), round(c['alpha'], 3),
                    '#%02x%02x%02x' % tuple(round(v) for v in eff))
        pg.close()
        br.close()
    return out


if not HAVE:
    skip('sections 6 and 7', 'playwright is not installed')
else:
    ok(bool(boot), 'the bootstrap 4.1.3 fixture is on disk')
    ok(bool(bcss), '  and base\'s stylesheet came through')
    ok(bool(binder), '  and base\'s menu binder is in the fixture')
    ok(HAVE_PIL, '  and PIL is available to read the pixels')

# ==========================================================================
head('6. THE HEADLINE - THE PAGE COULD NOT BE USED FROM A KEYBOARD')
# ==========================================================================
if not HAVE:
    skip('section 6', 'no browser')
else:
    b_desk = probe(OLD, 1280, 'before_desk')
    a_desk = probe(SRC, 1280, 'after_desk')
    a_armed = probe(SRC, 1280, 'after_armed', choose=True)

    bf, af, am = b_desk['focus'], a_desk['focus'], a_armed['focus']

    ok(bf['tiles'] == 0,
       'BEFORE: %d of %d tiles were keyboard-reachable' % (bf['tiles'], TILES),
       bf)
    ok(bf['rows'] == 0, '  BEFORE: 0 picker rows were keyboard-reachable')
    ok(bf['chooser'] == 0,
       '  BEFORE: the property could not be chosen from a keyboard at all')
    print('        Tab through the Property Dashboard as it was and you')
    print('        reached the hamburger and the Back link. That was all.')
    print('        The selector, the twelve tiles and every picker row')
    print('        were divs with a click listener and no key handling.')

    ok(af['chooser'] == 1,
       'AFTER: Choose Property is one keyboard-reachable control')
    ok(af['rows'] >= 1,
       '  AFTER: the picker rows are buttons and reachable', af['rows'])
    ok(af['tiles'] == 0 and af['hrefs'] == 0,
       '  AFTER, unarmed: still 0 reachable tiles - WHICH IS CORRECT')
    print('        An <a> with no href is neither focusable nor')
    print('        clickable. That is the lock, and it is a lock a')
    print('        keyboard obeys - which pointer-events never was.')

    ok(am['hrefs'] == TILES,
       '  AFTER, once a property is chosen: all %d tiles have an href'
       % TILES, am['hrefs'])
    ok(am['tiles'] == TILES,
       '    and all %d are keyboard-reachable' % TILES, am['tiles'])
    ok(am['visible'] > bf['visible'],
       '  keyboard-reachable controls on the page: %d -> %d'
       % (bf['visible'], am['visible']))
    print('        Section 6 drove the page\'s OWN selectProperty by')
    print('        clicking a real picker row - not a reimplementation')
    print('        of it - so what is measured is the shipped handler.')

    # CONTROL: the twin must NOT have become reachable. A disabled tile
    # that takes focus is a worse bug than one that cannot be read.
    ok(am['tiles'] == TILES,
       '  CONTROL: the twin is not among them - %d, not %d'
       % (am['tiles'], TILES + 1))

    a_ph = probe(SRC, 390, 'after_phone', choose=True)
    ok(a_ph['focus']['tiles'] == TILES,
       'and the same on a phone at 390px', a_ph['focus'])

    # ------------------------------------------------------------------
    # AND THE BAR ITSELF, AT BOTH WIDTHS. Section 3 argues from base's
    # source that the More menu is a phone component and Help therefore
    # has to be a desktop secondary. This is that argument on screen -
    # and it is the check that would catch the regression, because a
    # page whose Help is reachable at neither width looks fine in a
    # screenshot taken at the other one.
    for w, want in ((1280, {'secondary': True, 'more': False}),
                    (390, {'secondary': False, 'more': True})):
        bar = probe(SRC, w, 'bar%d' % w)['bar']
        if not bar:
            ok(False, 'the bar rendered at %dpx' % w)
            continue
        kids = {k['kind']: k for k in bar}
        ok(kids.get('primary', {}).get('vis'),
           '%4dpx  Choose Property is visible' % w, bar)
        ok(kids.get('secondary', {}).get('vis') == want['secondary'],
           '  Help as a desktop secondary: %s'
           % ('shown' if want['secondary'] else 'hidden, base hides it'),
           kids.get('secondary'))
        ok(kids.get('more', {}).get('vis') == want['more'],
           '  the More menu: %s'
           % ('shown' if want['more'] else 'hidden, base hides it'),
           kids.get('more'))
        ok(kids.get('back', {}).get('vis'), '  Back is visible', kids.get('back'))
        if w == 390:
            ok(kids['back']['w'] == 44 and kids['back']['h'] == 44,
               '    as a 44px square, which is base\'s phone rule',
               kids['back'])
            ok(kids['more']['w'] == 44 and kids['more']['h'] == 44,
               '    and so is More', kids['more'])
            ok(kids['primary']['h'] == 44,
               '    and the primary is 44px tall', kids['primary'])
    print('        HELP IS REACHABLE AT BOTH WIDTHS, by different')
    print('        controls - which is why the hamburger disappearing')
    print('        on a desktop is the answer and not a loss.')

# ==========================================================================
head('7. READ OFF THE SCREEN, BECAUSE NO GATE HERE READS opacity')
# ==========================================================================
if not HAVE or not HAVE_PIL:
    skip('section 7', 'no browser, or no PIL')
else:
    # THE CLAIM THIS SECTION RESTS ON, PROVED FIRST.
    for s in ('test_pair_contrast.py', 'test_contrast.py'):
        p = os.path.join(ROOT, s)
        if not os.path.isfile(p):
            skip(s, 'not on disk')
            continue
        ok('opacity' not in read(p),
           '%s does not contain the word opacity' % s)
    print('        Every contrast gate in this system reads DECLARED')
    print('        colour pairs. The page dimmed four times with')
    print('        opacity, so all four passed every sweep. That is why')
    print('        this section screenshots the label and asks the')
    print('        image instead of asking the CSS.')

    bs, as_ = b_desk['shots'], a_desk['shots']
    # (a) THE LABEL, FROM THE IMAGE.
    if 'tile_label' in bs and 'tile_label' in as_:
        rb, ra = bs['tile_label'], as_['tile_label']
        ok(ra[0] > rb[0],
           'the tile label on the page you LAND on, FROM PIXELS: '
           '%.2f:1 -> %.2f:1   (%s on %s)' % (rb[0], ra[0], ra[1], ra[2]))
        ok(ra[0] >= 4.5,
           '  and it meets the 4.5:1 floor for body text now',
           '%.2f:1' % ra[0])
        ok(rb[0] < 4.5, '  CONTROL: it did not before', '%.2f:1' % rb[0])
    else:
        skip('the tile label', 'not rendered')

    # (b) THE ICON, FROM THE RESOLVED CASCADE - see COMPOSITE above for
    #     why there are no pixels to read for a webfont glyph.
    bc, ac = b_desk['cascade'], a_desk['cascade']
    if 'tile_icon' in bc and 'tile_icon' in ac:
        rb, ra = bc['tile_icon'], ac['tile_icon']
        ok(rb[1] < ra[1],
           'the accent icon, FROM THE RESOLVED OPACITY CHAIN: alpha '
           '%.2f -> %.2f' % (rb[1], ra[1]))
        ok(ra[0] > rb[0],
           '  %.2f:1 -> %.2f:1   (%s on paper)' % (rb[0], ra[0], ra[2]))
        ok(ra[0] >= 3.0,
           '  and it meets the 3.0:1 floor for a non-text element',
           '%.2f:1' % ra[0])
        ok(rb[0] < 3.0, '  CONTROL: it did not before', '%.2f:1' % rb[0])
    else:
        skip('the accent icon', 'the cascade probe found nothing')

    # (c) AND THE TWO INSTRUMENTS AGREE ON THE ONE THING BOTH CAN SEE.
    #     A pixel read and a cascade composite are different methods; if
    #     they disagreed about the label, one of them would be wrong and
    #     every number in this section would be worth nothing.
    if 'tile_label' in as_ and 'tile_label' in ac:
        ok(abs(as_['tile_label'][0] - ac['tile_label'][0]) < 0.6,
           '  CONTROL: pixels and cascade agree on the label - %.2f:1 '
           'and %.2f:1' % (as_['tile_label'][0], ac['tile_label'][0]),
           '%s vs %s' % (as_['tile_label'], ac['tile_label']))
    print('        0.75 is not a taste. Measured at every step, the')
    print('        accent icon clears 3.0 at .75 and fails at .70')
    print('        (2.90). It is the LOWEST dim that keeps the signal')
    print('        and meets the floor.')

    if 'twin_label' in bs and 'twin_label' in as_:
        rb, ra = bs['twin_label'], as_['twin_label']
        ok(ra[0] > rb[0],
           'the PERMISSION-DENIED tile: %.2f:1 -> %.2f:1   (%s on %s)'
           % (rb[0], ra[0], ra[1], ra[2]))
        ok(rb[0] < 2.0,
           '  CONTROL: it really was unreadable - dimmed TWICE, #adb5bd '
           'text AND opacity 0.5', '%.2f:1' % rb[0])
        ok(ra[0] >= 4.5,
           '  and it reads now', '%.2f:1' % ra[0])
        print('        A user without the permission could not read what')
        print('        they were being denied. E-10\'s lesson from the')
        print('        other side: there a switched-off button was the')
        print('        only one in the app that was not grey.')
    else:
        skip('the twin', 'the fixture rendered no disabled tile')

# ==========================================================================
head('8. THE TWO SUITES THIS ROUND DOES NOT TOUCH, AND WHY')
# ==========================================================================
# test_more_css carries this page on a SKIP list - "an always-present
# side hamburger, outside any .page-action-buttons" - and PROVES the
# exclusion by stripping the local rules in a fixture: 56x36 -> GONE on
# a desktop. test_last_menus calls it PAINTER, "the one page that still
# paints the component". Both reasons stop being true of the LIVE file
# today. NEITHER SUITE IS CHANGED, and that is a measurement.
MC, LM = 'test_more_css.py', 'test_last_menus.py'
for s, token in ((MC, "'property_management_dashboard.html':"),
                 (LM, "PAINTER = 'property_management_dashboard.html'")):
    p = os.path.join(ROOT, s)
    if not os.path.isfile(p):
        skip(s, 'not on disk')
        continue
    ok(token in read(p),
       '%s still names this page, untouched by DB-5' % s)
    ok(not os.path.isfile(p + SUFFIX),
       '  and DB-5 took no backup of it - it did not edit it')

if as_left_by:
    for suf in ('.bak_morecss', '.bak_lastmenu'):
        seen = as_left_by(P, suf, read)
        ok(seen != SRC,
           'as_left_by(dash, %s) returns HISTORY, not the live file' % suf)
        ok('dashboard-side-actions' in seen,
           '  so %s still sees the side column it was written against'
           % suf)
    print('        The dashboard already carried six backups later than')
    print('        .bak_morecss - the earliest is .bak_msgbar - so both')
    print('        suites have been reading history since well before')
    print('        today. Their recorded reasons are measurements of')
    print('        their own moment and stay true for it.')
    print('        A round that rewrote them because the live file')
    print('        moved would be the as_left_by lesson from the wrong')
    print('        side for the FOURTH time.')

    # AND THE PINNED COUNTS THAT WOULD HAVE MOVED. test_accent_ink pins
    # 3 accent-ink uses on this page and test_line_soft pins 1 + 1 -
    # three of the four accent-ink uses were in rules DB-5 deleted. They
    # do not move, because those suites read the page as their own round
    # left it, and registering DB-5 LAST is what guarantees that.
    # THE PINS ARE READ OUT OF THOSE SUITES, NOT RETYPED HERE. The
    # first draft of these two checks asserted 4 and 2 - the counts in
    # the LIVE pre-DB-5 file - and both failed, because as_left_by
    # returns the page as ACCENT-INK left it, which is an earlier state
    # with 3 and 1. The suites pin 3 and 1. Asking the suite what it
    # pins is the only version of this check that cannot drift.
    for suf, tok, src in (('.bak_accentink', 'var(--alv-accent-ink)',
                           'test_accent_ink.py'),
                          ('.bak_linesoft', 'var(--alv-line-soft)',
                           'test_line_soft.py')):
        sp = os.path.join(ROOT, src)
        if not os.path.isfile(sp):
            skip(src, 'not on disk')
            continue
        m = re.search(r"'property_management_dashboard\.html':\s*(\d+)",
                      read(sp))
        if not m:
            ok(False, '%s pins a count for this page' % src)
            continue
        pin = int(m.group(1))
        seen = as_left_by(P, suf, read).count(tok)
        ok(seen == pin,
           '%s pins %d %s here, and as_left_by still answers %d'
           % (src, pin, tok, seen), '%d vs %d' % (seen, pin))
    ok(SRC.count('var(--alv-accent-ink)') == 1,
       '  CONTROL: the LIVE file has 1, because DB-5 deleted three of '
       'the four rules that held them', SRC.count('var(--alv-accent-ink)'))

# ==========================================================================
head('9. REGISTERED, ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok('the landing dim stays at the measured 0.75' in ps,
   '  and a sentinel refuses the landing dim going back to 0.45')
ok("Text = 'pointer-events: none'" not in ps,
   '    CONTROL: and it does NOT assert the absence of pointer-events')
print('        The first version of that row did, and the permission-')
print('        denied TWIN keeps that declaration on purpose - so the')
print('        sentinel asserted the absence of a string that must be')
print('        present, and took ten suites down with it. A control')
print('        that cannot pass is as bad as one that cannot fail.')

# A PowerShell array literal's last row carries no comma. E-10 shipped
# one that did, the gate would not parse, and NO suite could have caught
# it - the file that will not start is the file that runs the suites. So
# the structure is read back rather than assumed. And the first version
# of this guard was itself wrong: it demanded a comma on EVERY row and
# refused on three pre-existing ones, because a newline separates
# elements inside @() just as a comma does. A rule invented rather than
# measured, twice in one round.
blk = ps[ps.index('$sentinels = @('):]
blk = blk[:blk.index('\n)\n')]
rows = [ln.rstrip() for ln in blk.split('\n')
        if ln.strip() and not ln.strip().startswith('#')]
ok(not rows[-1].endswith(','),
   '  and $sentinels does not end in a comma', rows[-1][-46:])

wd = os.path.join(ROOT, 'test_waiting_down.py')
if os.path.isfile(wd):
    w = read(wd)
    ok('CONVERTED_N = 67' in w,
       'CONVERTED_N is 67 - this round\'s own suite joined')
    ok('CEILING = 40' in w,
       '  and the ceiling does NOT move: DB-5 converted no existing '
       'suite, so there is no census to take off the count')

# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if skipped:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.'
          % skipped)
print('')
print('  NOT PROVED HERE: that any of the twelve destinations is right.')
print('  The two URL shapes moved from a click handler into a function')
print('  unchanged, and this round did not touch routing. Nor that 0.75')
print('  is the dim Demetri will want - it is the lowest value that')
print('  meets the floor, which is a floor and not a preference. Nor')
print('  that a house TILE component should exist: base has none, six')
print('  pages draw one under six private names, and that is a real')
print('  question which one page does not get to answer.')
sys.exit(1 if failed else 0)
