# -*- coding: utf-8 -*-
"""FG-1 - .filter-grid FINISHES THE JOB IT STARTS

Demetri, 3 Oct 2026, of the filters going into the Recipes module: "The
filter fields must be made less wide, so that they fit on one line."

Measuring every filter panel in the tree to find out which one he meant
turned up something worse than wide fields on the page the Recipes
programme has already delivered.

==========================================================================
IB-1 SHIPPED A STACKED PANEL YESTERDAY, AND base IS WHY
==========================================================================
ingredient_base_units_management, at a 1920 screen:

    2 fields, on 2 rows, widest control 1888px

Two fields stacked one above the other, each the full width of the panel.
A search box nearly a metre across.

The page is not at fault for omitting anything a page is supposed to
supply. base declares:

    .filter-grid { display: grid; gap: 20px; align-items: end; }

display: grid and NO grid-template-columns. A grid with no columns
declared is a grid with ONE column, so every child stacks and each one
fills the track. The component only works if its caller remembers to
finish it, and the first caller that did not got a stacked panel.

==========================================================================
IT MOVES EXACTLY ONE EXISTING PAGE, AND THAT IS MEASURED
==========================================================================
Fifteen templates carry a .filter-grid. TWELVE of them set their own
grid-template-columns and are completely unaffected by a default - a
declaration in base is (0,1,0) and a page's own copy, written later in
the document, wins every time.

Of the other three, two - passport_management and recipe_management - do
not use .filter-grid at all; they have .passport-filter-grid and
.recipe-filter-grid, their own classes.

Which leaves ONE page in the entire tree relying on base for its columns,
and it is the broken one. The gate below counts this rather than claiming
it, and renders the twelve before and after to prove none of them moved.

==========================================================================
THE RECIPE
==========================================================================
    grid-template-columns: repeat(auto-fit, minmax(200px, 240px));
    justify-content: start;

  auto-fit         the browser decides how many fit; a page does not have
                   to re-count its columns every time a field is added
  minmax(200, 240) a floor so a field is never unusably narrow, and a CAP
                   so it never stretches into a banner. This is the half
                   Demetri asked for.
  justify-content  pack from the left. Without it the slack is spread
                   BETWEEN the fields and two fields sit at opposite ends
                   of the panel with a metre of nothing between them.

  under 768px      one column, full width, as every filter panel in the
                   tree already does - a 240px cap on a 358px phone would
                   waste a third of the screen.

Backups: .bak_filtergrid. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_filtergrid'
ROOT = os.getcwd()
CRLF = {}
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

CAP = 240
FLOOR = 200


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('FG1: %s is not a byte copy' % bak)


def swap(path, text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('FG1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('FG-1 - .filter-grid FINISHES THE JOB IT STARTS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(BASE)

if 'auto-fit, minmax(%dpx, %dpx)' % (FLOOR, CAP) in t:
    print('  base.html                  .filter-grid already declares columns')
else:
    t = swap(BASE, t, """.filter-grid {
    display: grid;
    gap: 20px;
    align-items: end;
}""",
             """.filter-grid {
    display: grid;
    gap: 20px;
    align-items: end;
    /* COLUMNS - FG-1, 3 Oct 2026, and the reason this round exists.
       This rule declared display: grid and no columns, which is a grid
       with ONE column: every field stacks and each one fills the track.
       It worked anyway for a year because all twelve pages using it set
       their own grid-template-columns - and then IB-1 shipped a page
       that did not, and its two fields rendered stacked, 1888px wide
       each, on a 1920 screen.

       A component that only behaves when its caller remembers to finish
       it is not finished. So the default is here now, and a page that
       sets its own still wins - a declaration here is (0,1,0) and a
       page's copy comes later in the document.

       auto-fit lets the browser count the columns, so a panel that
       gains a field does not need its track list rewritten. The floor
       keeps a field usable; the CAP is what Demetri asked for on 3 Oct:
       "the filter fields must be made less wide, so that they fit on
       one line". Without justify-content the slack is shared BETWEEN
       the tracks and two fields sit at opposite ends of the panel. */
    grid-template-columns: repeat(auto-fit, minmax(%dpx, %dpx));
    justify-content: start;
}

/* ONE COLUMN ON A PHONE. A 240px cap on a 358px screen would leave a
   third of the width empty, and every filter panel in the tree already
   goes single-column here. */
@media screen and (max-width: 768px) {
    .filter-grid {
        grid-template-columns: 1fr;
    }
}""" % (FLOOR, CAP),
             'the filter-grid rule')

    if not CHECK:
        back_up(BASE, raw)
        write(BASE, t)
    print('  base.html                  .filter-grid declares columns, capped '
          'at %dpx' % CAP)

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import alv_tree

NOW = read(BASE)[0]
WAS = read(BASE + SUFFIX)[0]


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def nocomment(t):
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def sets_columns(css):
    """Rules whose SELECTOR carries the token filter-grid and which set
    grid-template-columns. A class is a token: .recipe-filter-grid is not
    .filter-grid, and a substring test says it is."""
    n = 0
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', nocomment(css)):
        if (re.search(r'\.filter-grid(?![-\w])', m.group(1))
                and 'grid-template-columns' in m.group(2)):
            n += 1
    return n


# 1. THE DECLARATION IS THERE, AND SO IS THE PHONE OVERRIDE.
bcss = nocomment(css_of(NOW))
if 'repeat(auto-fit, minmax(%dpx, %dpx))' % (FLOOR, CAP) not in bcss:
    raise SystemExit('FG1: the track list is not in base')
if 'justify-content: start' not in bcss:
    raise SystemExit('FG1: without justify-content the slack spreads between '
                     'the fields and two of them sit at opposite ends')
if sets_columns(css_of(NOW)) < 2:
    raise SystemExit('FG1: expected the default and the phone override')
print('  base declares the track list, packs from the left, and goes one '
      'column on a phone')

# 2. THE PREMISE: base really did declare a grid with no columns.
if sets_columns(css_of(WAS)) != 0:
    raise SystemExit('FG1: base already set columns - the premise of this '
                     'round is wrong')
if 'display: grid' not in nocomment(css_of(WAS)):
    raise SystemExit('FG1: .filter-grid was not a grid at all')
print('  CONTROL: it really did declare display: grid and no columns')

# 3. HOW MANY PAGES THIS MOVES - COUNTED, NOT CLAIMED.
users, own, foreign = [], [], []
for rel in sorted(alv_tree.templates()):
    src = open(alv_tree.path_of(rel), encoding='utf-8',
               errors='replace').read()
    # A CLASS IS A TOKEN, NOT A SUBSTRING - and \b IS NOT A TOKEN
    # BOUNDARY WHEN THE NEIGHBOUR IS A HYPHEN. The first cut of this gate
    # used r'class="[^"]*\bfilter-grid\b' and matched
    # class="passport-filter-grid" and class="recipe-filter-grid", because
    # \b sits happily between '-' and 'f'. It then reported that this
    # round moved three pages instead of one.
    #
    # Twenty-first time this week, and this patcher's own note two
    # screens up says "a class is a token: .recipe-filter-grid is not
    # .filter-grid, and a substring test says it is" - about the CSS
    # side, while the markup side beside it was doing exactly that.
    classes = set()
    for m in re.finditer(r'class="([^"]*)"', src):
        classes.update(m.group(1).split())
    if 'filter-grid' not in classes:
        if re.search(r'filter-grid', src):
            foreign.append(rel)
        continue
    users.append(rel)
    if sets_columns(css_of(src)):
        own.append(rel)
moved = [p for p in users if p not in own]
print('  %d templates use .filter-grid; %d set their own columns'
      % (len(users), len(own)))
for p in moved:
    print('    MOVED BY THIS ROUND: %s' % p)
if len(moved) != 1:
    raise SystemExit('FG1: this round moves %d pages, expected exactly one - '
                     'the broken one:\n   %s' % (len(moved),
                                                 '\n   '.join(moved)))
if 'ingredient_base_units_management' not in moved[0]:
    raise SystemExit('FG1: the page it moves is %s, not the one measured as '
                     'broken' % moved[0])
print('  and it is the page measured as stacked - no other page moves')

# 4. THE TWELVE, RENDERED BEFORE AND AFTER. A specificity argument is a
#    claim about a cascade; this is the cascade, run.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  -- the twelve-page render (playwright not installed)')
    sync_playwright = None

if sync_playwright is not None:
    FIXP = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
    FIX = open(FIXP, encoding='utf-8', errors='replace').read() \
        if os.path.exists(FIXP) else ''
    IF_ELSE = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*else\s*%\}.*?'
                         r'\{%\s*endif\s*%\}', re.S)
    IF_ONLY = re.compile(r'\{%\s*if\b.*?%\}(.*?)\{%\s*endif\s*%\}', re.S)
    FOR = re.compile(r'\{%\s*for\b.*?%\}(.*?)\{%\s*endfor\s*%\}', re.S)
    ANYT = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)

    def resolve(h):
        for pat in (IF_ELSE, IF_ONLY, FOR):
            prev = None
            while prev != h:
                prev = h
                h = pat.sub(lambda m: m.group(1), h)
        return ANYT.sub('', h)

    def panel_of(src):
        # A CLASS IS A TOKEN. Looking for the string 'class="alv-filter'
        # matched class="alv-filter-active" - the chip row, which holds no
        # fields - on all fifteen pages, and the measurement that found
        # this bug first reported that no page in the tree had a grid.
        i = -1
        for m in re.finditer(r'class="([^"]*)"', src):
            if 'alv-filter' in m.group(1).split():
                i = m.start()
                break
        if i < 0:
            return None
        i = src.rindex('<div', 0, i)
        depth, j = 0, i
        tag = re.compile(r'</?div\b')
        while True:
            m = tag.search(src, j)
            if not m:
                return None
            depth += 1 if src[m.start():m.start() + 2] == '<d' else -1
            j = m.end()
            if depth == 0:
                break
        j = src.index('>', j - 1) + 1
        return resolve(src[i:j]).replace('class="alv-filter',
                                         'class="is-open alv-filter')

    PROBE = """() => {
      const g = document.querySelector('.filter-grid');
      if (!g) return null;
      const k = [...g.children];
      /* BOTTOM, NOT TOP - .filter-grid sets align-items: end, so two
         groups of different heights on the SAME row have different tops
         and the same bottom. Counting tops reported two rows for panels
         the browser had laid out on one. */
      const b = new Set(k.map(e =>
          Math.round(e.getBoundingClientRect().bottom)));
      return {rows: b.size, n: k.length, widest: Math.max(...k.map(e => {
        const c = e.querySelector('input,select,textarea');
        return c ? Math.round(c.getBoundingClientRect().width) : 0;
      }))};
    }"""

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def measure(page_css, html, basecss, w):
            doc = ('<!doctype html><meta charset=utf-8>'
                   '<style>%s</style><style>%s</style><style>%s</style>'
                   '<style>body{margin:0;padding:16px}</style><body>%s'
                   % (FIX, basecss, page_css, html))
            pg.set_viewport_size({'width': w, 'height': 600})
            pg.set_content(doc, wait_until='domcontentloaded')
            return pg.evaluate(PROBE)

        bnow, bwas = css_of(NOW), css_of(WAS)
        drifted = []
        for rel in users:
            src = open(alv_tree.path_of(rel), encoding='utf-8',
                       errors='replace').read()
            html = panel_of(src)
            if not html:
                raise SystemExit('FG1: could not slice the panel on %s - an '
                                 'unmeasured page is not an unmoved one'
                                 % rel)
            pcss = css_of(src)
            for w in (1920, 1280, 390):
                a = measure(pcss, html, bwas, w)
                b = measure(pcss, html, bnow, w)
                if rel in own and a != b:
                    drifted.append('%s @%d  %s -> %s' % (rel, w, a, b))
                if rel not in own:
                    print('    %s @%d  %d field(s) on %d row(s) widest %dpx'
                          '  ->  %d row(s) widest %dpx'
                          % (os.path.basename(rel), w, a['n'], a['rows'],
                             a['widest'], b['rows'], b['widest']))
        br.close()

    if drifted:
        raise SystemExit('FG1: %d page/width pairs moved that should not '
                         'have:\n   %s' % (len(drifted),
                                           '\n   '.join(drifted[:6])))
    print('  all %d pages that set their own columns render IDENTICALLY '
          'before and after, at 1920, 1280 and 390' % len(own))

print('-' * 74)
print('  A component that only behaves when its caller remembers to')
print('  finish it is not finished. Twelve callers remembered; the')
print('  thirteenth shipped a stacked panel.')
print('=' * 74)
