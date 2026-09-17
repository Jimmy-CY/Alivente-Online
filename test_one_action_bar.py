"""test_one_action_bar.py - there is one action bar, it sits at the top of
   the form, and the variant that was removed really did nothing.

    python test_one_action_bar.py

Run from the repo root, after apply_one_action_bar.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you Save belongs at the top rather than the bottom. That was
decided on 16 Sep, looking at the two rendered side by side. Five screens
moved. This suite holds the system to one answer; it does not argue for it.

SECTION 3 IS THE ONE THAT EARNS ITS KEEP, AND IT IS AN ODD SHAPE: it puts
the deleted rules BACK, in an injected stylesheet, and measures whether
they change anything. That is the entire case for having deleted them, and
it is a claim about CSS that no amount of reading can settle - specificity
is equal between the variant's justify-content and the auto margin base
puts on .action-back, and which one wins is a fact about the layout
algorithm rather than about the cascade.

It also measures the case where the rules DO bite - a bar with no Back
button - so the measurement cannot be passing vacuously. And it reports
what the rules WERE worth: one pixel of vertical alignment below 768px,
which is the whole behavioural difference the retirement removed.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)

CLS = 'page-action-buttons-form'

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

ENTRY = re.compile(r'(_add|_edit|_form)\.html$|(^|/)generate_')

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}

# The rules that were removed, restored verbatim for section 3.
REMOVED = """
.page-action-buttons-form { justify-content: flex-end; }
@media screen and (max-width: 768px) {
  .page-action-buttons-form { display: flex; flex-direction: row; gap: 8px;
    width: 100%; flex-wrap: nowrap; align-items: stretch;
    margin-bottom: 1rem; }
  .page-action-buttons-form .action-primary { flex: 1 1 auto; min-width: 0;
    height: 38px; display: flex; align-items: center;
    justify-content: center; text-align: center; padding: 0 12px;
    font-size: 13px; white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis; margin: 0; }
  .page-action-buttons-form .action-back { flex: 0 0 auto; width: 44px;
    height: 38px; padding: 0; display: flex; align-items: center;
    justify-content: center; margin: 0; }
}
"""

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def skip(name, why):
    global SKIP
    SKIP += 1
    print('  SKIP  %s - %s' % (name, why))


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out, flags=re.S)


def templates():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if n.endswith('.html'):
                path = os.path.join(dirpath, n)
                out.append((os.path.relpath(path, T).replace(os.sep, '/'),
                            path))
    return sorted(out)


def close_of(scan, open_end, tag):
    depth, i = 1, open_end
    pat = re.compile(r'<(/?)%s\b[^>]*>' % tag, re.I)
    while True:
        m = pat.search(scan, i)
        if not m:
            return None
        depth += -1 if m.group(1) else 1
        i = m.end()
        if depth == 0:
            return m.end()


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

B = read(BASE)

# ---------------------------------------------------------------------- 1
head('1. THE VARIANT IS GONE')

# A CLASS TOKEN OR A RULE, NEVER THE BARE STRING - base's own note names
# the class it retired, and a substring search calls that a survival.
USE = re.compile(r'class="[^"]*(?<![-\w])%s(?![-\w])' % re.escape(CLS))
RULE = re.compile(r'\.%s\b[^{}\n]*\{' % re.escape(CLS))

carriers = []
for rel, path in templates():
    t = read(path)
    if USE.search(t) or RULE.search(t):
        carriers.append(rel)
check('no template declares or uses the retired variant', not carriers,
      '%d: %s' % (len(carriers), ', '.join(carriers[:4])))
check('  CONTROL: the check sees a class token when there is one',
      bool(USE.search('class="a %s b"' % CLS))
      and not USE.search('class="%s-x"' % CLS)
      and bool(RULE.search('.%s { a: b; }' % CLS)))
check('base says why it went', 'THERE IS ONE ACTION BAR' in B)
check('  and still declares the bar that remains',
      bool(re.search(r'\.page-action-buttons\s*\{', B)))

# ---------------------------------------------------------------------- 2
head('2. THE BAR IS THE FIRST THING IN THE FORM')

# THE CLAIM IS "SAVE IS AT THE TOP", NOT "THE BAR IS INSIDE THE FORM".
# The first spelling required the bar to sit inside the <form> and to be
# the first thing in it. Eight screens put their bar ABOVE the form
# element and two put a heading inside the form above it - both perfectly
# ordinary arrangements that put Save exactly where the decision says.
# What the decision was about is what the READER sees first, so that is
# what this measures: the bar comes before the first control.
late, nobar = [], []
screens = 0
for rel, path in templates():
    if any(x in rel for x in RECIPE) or rel == 'base.html':
        continue
    t_ = read(path)
    if '<form' not in t_ or 'form-control' not in t_ or not ENTRY.search(rel):
        continue
    screens += 1
    scan = inert(t_)
    bar = re.search(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b[^"]*"[^>]*>',
                    scan, re.I)
    ctrl = re.search(r'class="[^"]*\bform-control\b', scan)
    if not bar:
        nobar.append(rel)
        continue
    if ctrl and bar.start() > ctrl.start():
        late.append(rel)

print('        %d Add/Edit screen(s).' % screens)
for rel in late:
    print('          a control appears above the bar: %s' % rel)
for rel in nobar:
    print('          no action bar: %s' % rel)
check('the action bar comes before the first control on every screen',
      not late, '%d do not: %s' % (len(late), ', '.join(late[:4])))
check('  CONTROL: and there are bars to have placed wrongly',
      screens - len(nobar) >= 15, '%d bar(s)' % (screens - len(nobar)))
check('  every Add/Edit screen has one at all', not nobar,
      '%d have none: %s' % (len(nobar), ', '.join(nobar[:4])))

# ---------------------------------------------------------------------- 3
head('3. RENDERED - the removed rules really did nothing')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

if sync_playwright is None:
    skip('restoring them changes no button\'s position or size',
         'playwright is not installed')
    skip('CONTROL: they DO move a bar that has no Back button',
         'playwright is not installed')
else:
    cut = B.find('{% block content %}')
    pre, post = [], []
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', B, re.S):
        (pre if m.end(1) < cut else post).append(m.group(1))

    def bar(extra, secondaries, back):
        h = '<div class="page-action-buttons %s">' % extra
        h += '<button class="btn action-primary">Save</button>'
        for i in range(secondaries):
            h += '<button class="btn action-secondary">S%d</button>' % i
        if back:
            h += ('<a href="#" class="btn action-back">'
                  '<span class="action-back-label">Back</span></a>')
        return h + '</div>'

    def geom(pg, html, restore):
        doc = ('<!doctype html><meta charset=utf-8><style>%s</style>%s'
               '<style>%s</style>%s'
               % ('\n'.join(pre), html, '\n'.join(post),
                  '<style>%s</style>' % REMOVED if restore else ''))
        pg.set_content(doc, wait_until='load')
        return pg.evaluate("""() => {
            const b = document.querySelector('.page-action-buttons');
            const r0 = b.getBoundingClientRect();
            return [...b.children].map(e => {
                const r = e.getBoundingClientRect();
                return [Math.round(r.left), Math.round(r.top - r0.top),
                        Math.round(r.width), Math.round(r.height)].join(',');
            }).join(' | ');
        }""")

    try:
        # WHAT IS ACTUALLY TRUE, measured rather than asserted. On DESKTOP
        # the removed rules change nothing at all. On a PHONE they change
        # one thing: align-items: stretch instead of the plain bar's
        # centre, which sits the 38px buttons 1px higher beside the 40px
        # Back button. That 1px is the entire behavioural difference the
        # retirement removed, and the first spelling of this section
        # claimed there was none - which the browser immediately
        # contradicted at two of the three widths.
        hdiff, vmax = [], 0
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            for w in (1040, 768, 400):
                pg = br.new_page(viewport={'width': w, 'height': 400})
                pg.route('**://**', lambda r: r.abort())
                for n in (0, 1, 3):
                    a = geom(pg, bar('', n, True), False).split(' | ')
                    b2 = geom(pg, bar(CLS, n, True), True).split(' | ')
                    for x, y in zip(a, b2):
                        xa, ya = x.split(','), y.split(',')
                        if (xa[0], xa[2], xa[3]) != (ya[0], ya[2], ya[3]):
                            hdiff.append('%dpx/%d' % (w, n))
                        vmax = max(vmax, abs(int(xa[1]) - int(ya[1])))
                if w == 1040:
                    noback = (geom(pg, bar('', 1, False), False)
                              != geom(pg, bar(CLS, 1, False), True))
                pg.close()
            br.close()
        print('        the removed rules move nothing horizontally at any')
        print('        width; the largest vertical shift they caused was '
              '%dpx.' % vmax)
        check('restoring them changes no button\'s position or size',
              not hdiff, '%d shape(s) differ: %s'
              % (len(hdiff), ', '.join(sorted(set(hdiff)))))
        check('  and the vertical difference is the 1px they were worth',
              vmax <= 1, '%dpx' % vmax)
        check('CONTROL: they DO move a bar that has no Back button', noback,
              'otherwise this section is measuring nothing')
    except Exception as e:
        for n in ('restoring them changes no button\'s position or size',
                  'CONTROL: they DO move a bar that has no Back button'):
            skip(n, 'the browser would not run: %s' % str(e)[:40])

# ---------------------------------------------------------------------- 4
head('4. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    check('this suite is on the gate', ME in read(PS1), ME)

# ---------------------------------------------------------------------- 5
print('\n' + '=' * 72)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
if FAILED:
    print('')
    for f in FAILED:
        print('  - %s' % f)
if SKIP:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.' % SKIP)
print('')
print('  NOT PROVED HERE: that Save belongs at the top. That was decided on')
print('  16 Sep from the two rendered side by side. This holds the system')
print('  to one answer rather than two.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
