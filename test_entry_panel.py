"""test_entry_panel.py - every Add and Edit screen has a panel, and it is
   the one base declares.

    python test_entry_panel.py

Run from the repo root, after apply_entry_panel.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you the fields are grouped WELL. Each swept screen has one
panel around everything, which is mechanical and safe. The model screen
has three, titled - Customer, Settings, Lines - and deciding which fields
belong together on any other screen is design work a tool cannot do. This
suite proves the panel is there and is the house one; it says nothing
about whether the screen is well organised.

SECTION 3 IS THE ONE THAT EARNS ITS KEEP. A wrap is a markup change on
signed-off pages, and the failure that would really hurt is invisible in
the diff: if a Django block tag opened inside the wrapped region and
closed outside it, the panel's closing tag would sit under a condition and
the page would come apart for one kind of user and not another. So this
suite checks the block tags of every entry screen balance, and checks the
panel opens and closes inside the same conditional depth.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
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

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

# WIDENED 17 Sep. The old pattern matched asset_edit.html and NOT
# edit_asset.html, so that screen was invisible to this round and to
# the two before it - and it was the one with Save at the bottom
# beside a redundant Cancel. A list of filenames is not a rule; a
# pattern that covers both spellings is.
ENTRY = re.compile(r'(^|/)(add|edit|new)_|(_add|_edit|_form|_new)\.html$'
                   r'|(^|/)generate_')

# The screens that carry a DIFFERENT box component and were deliberately
# left alone. NAMED, because a count cannot tell a new one from an old one,
# and each is a decision somebody has to take rather than a sweep.
OTHER_BOX = {
    'cash_receipt_add.html': 'the house .alv-card',
    'generate_lease_agreement.html': "Bootstrap's .card",
}

DJANGO_OPEN = ('if', 'for', 'with', 'block', 'comment', 'spaceless',
               'blocktrans', 'blocktranslate', 'autoescape', 'verbatim',
               'filter', 'ifchanged')

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
            if not n.endswith('.html'):
                continue
            path = os.path.join(dirpath, n)
            if os.path.abspath(path) == os.path.abspath(BASE):
                continue
            rel = os.path.relpath(path, T).replace(os.sep, '/')
            if any(t in rel for t in RECIPE):
                continue
            out.append((rel, path))
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


def cond_depth_at(text, pos):
    """How many Django block tags are open at this offset."""
    d = 0
    for m in re.finditer(r'\{%\s*(\w+)', text[:pos]):
        w = m.group(1)
        if w in DJANGO_OPEN:
            d += 1
        elif w.startswith('end'):
            d -= 1
    return d


def entry_screens():
    out = []
    for rel, path in templates():
        t = read(path)
        if '<form' not in t or 'form-control' not in t:
            continue
        if not ENTRY.search(rel):
            continue
        out.append((rel, t))
    return out


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

B = read(BASE)
SCREENS = entry_screens()

# ---------------------------------------------------------------------- 1
head('1. EVERY ADD AND EDIT SCREEN HAS THE HOUSE PANEL')

missing, panelled = [], []
for rel, t in SCREENS:
    if re.search(r'class="[^"]*\bform-card\b', inert(t)):
        panelled.append(rel)
    else:
        missing.append(rel)

print('        %d Add/Edit screen(s); %d carry .form-card.'
      % (len(SCREENS), len(panelled)))
for rel in missing:
    print('          no panel: %-40s %s'
          % (rel[:40], OTHER_BOX.get(rel.rsplit('/', 1)[-1], 'UNEXPLAINED')))

unexplained = [r for r in missing
               if r.rsplit('/', 1)[-1] not in OTHER_BOX]
check('every screen without a panel has a box of its own, and is named',
      not unexplained, '%d unexplained: %s'
      % (len(unexplained), ', '.join(unexplained[:4])))
check('  CONTROL: and most screens do carry it',
      len(panelled) >= len(SCREENS) - len(OTHER_BOX),
      '%d of %d' % (len(panelled), len(SCREENS)))
check('  no screen still calls its panel form-section',
      not any(re.search(r'(?<![-\w])form-section(?![-\w])', t)
              for _r, t in SCREENS))

# ---------------------------------------------------------------------- 2
head('2. THE PANEL IS WHERE THE MODEL SCREEN PUTS IT')

after_bar, before_bar, no_bar = [], [], []
for rel, t in SCREENS:
    scan = inert(t)
    p = re.search(r'<div\b[^>]*class="[^"]*\bform-card\b', scan)
    if not p:
        continue
    bar = re.search(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b', scan)
    if not bar:
        no_bar.append(rel)
    elif bar.start() < p.start():
        after_bar.append(rel)
    else:
        before_bar.append(rel)

print('        %d screen(s) put the action bar above the panel, %d below,'
      % (len(after_bar), len(before_bar)))
print('        %d have no action bar at all.' % len(no_bar))
for rel in before_bar:
    print('          panel above the bar: %s' % rel)
for rel in no_bar:
    print('          no action bar: %s' % rel)
# REPORTED, NOT FAILED - and the distinction is the point. The model
# screen puts Save and Back at the top right and the panel underneath.
# Five screens that already had a panel put the bar at the BOTTOM of the
# form instead. Moving it changes where the Save button lives, which is
# visible and preference-bearing: a decision somebody takes, not a fault a
# sweep corrects. It belongs to the action-bar round.
#
# What THIS round owns is that the panel sits inside the form it panels,
# which is what the wrap guarantees and what would break if the region had
# been chosen wrongly.
outside = []
for rel, t in SCREENS:
    scan = inert(t)
    p = re.search(r'<div\b[^>]*class="[^"]*\bform-card\b', scan)
    f = re.search(r'<form\b[^>]*>', scan, re.I)
    if not p or not f:
        continue
    fend = close_of(scan, f.end(), 'form')
    pend = close_of(scan, p.end(), 'div')
    if fend is None or pend is None:
        outside.append('%s (a tag never closes)' % rel)
        continue
    # EITHER NESTING IS FINE. customer_form puts the panel OUTSIDE its
    # form - the panel contains the form rather than the other way round -
    # and that is a legitimate arrangement, not a fault. The first
    # spelling of this check required the panel to be inside and reported
    # that page as broken. What must never happen is the two OVERLAPPING,
    # which is what a wrap chosen at the wrong offset would produce and
    # which no browser can recover from predictably.
    inside = f.end() < p.start() and pend <= fend
    around = p.end() < f.start() and fend <= pend
    if not (inside or around):
        outside.append(rel)
check('the panel and the form nest, rather than overlapping', not outside,
      '%d do not: %s' % (len(outside), ', '.join(outside[:4])))
check('  CONTROL: and there are panels to have placed wrongly',
      len(after_bar) + len(before_bar) + len(no_bar) >= 10,
      '%d panelled screen(s)'
      % (len(after_bar) + len(before_bar) + len(no_bar)))

# ---------------------------------------------------------------------- 3
head('3. THE PANEL OPENS AND CLOSES IN THE SAME CONDITION')

# THE FAILURE THAT WOULD REALLY HURT and is invisible in a diff: a panel
# opened inside an {% if %} and closed outside it closes only sometimes,
# so the page comes apart for one kind of user and not another. Nothing
# that reads the markup as a flat string can see it.
bad_depth, unbalanced = [], []
for rel, t in SCREENS:
    d = 0
    for m in re.finditer(r'\{%\s*(\w+)', t):
        w = m.group(1)
        if w in DJANGO_OPEN:
            d += 1
        elif w.startswith('end'):
            d -= 1
    if d != 0:
        unbalanced.append('%s (%+d)' % (rel, d))
    scan = inert(t)
    p = re.search(r'<div\b[^>]*class="[^"]*\bform-card\b[^"]*"[^>]*>', scan)
    if not p:
        continue
    end = close_of(scan, p.end(), 'div')
    if end is None:
        bad_depth.append('%s: the panel never closes' % rel)
        continue
    if cond_depth_at(t, p.start()) != cond_depth_at(t, end):
        bad_depth.append('%s: it opens and closes at different depths' % rel)

check('every Add/Edit screen\'s Django block tags balance', not unbalanced,
      '%d do not: %s' % (len(unbalanced), '; '.join(unbalanced[:3])))
check('  and every panel closes in the condition it opened in',
      not bad_depth, '; '.join(bad_depth[:3]))
check('  CONTROL: and there are screens with conditions to have got wrong',
      sum(1 for _r, t in SCREENS if '{% if' in t) >= 5,
      '%d screen(s) carry an {%% if %%}'
      % sum(1 for _r, t in SCREENS if '{% if' in t))

# ---------------------------------------------------------------------- 4
head('4. RENDERED - the panel actually carries the wash')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

if sync_playwright is None:
    skip('the panel renders the wash', 'playwright is not installed')
    skip('CONTROL: and a plain div does not', 'playwright is not installed')
else:
    cut = B.find('{% block content %}')
    pre, post = [], []
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', B, re.S):
        (pre if m.end(1) < cut else post).append(m.group(1))
    doc = ("<!doctype html><meta charset=utf-8><style>%s</style>"
           "<div class='form-card' id=p><div class='form-group'>"
           "<label for=x><strong>Field</strong></label>"
           "<input id=x class='form-control'></div></div>"
           "<div id=q>plain</div><style>%s</style>"
           % ('\n'.join(pre), '\n'.join(post)))
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1100, 'height': 700})
            pg.route('**://**', lambda r: r.abort())
            pg.set_content(doc, wait_until='load')
            m = pg.evaluate("""() => {
                const p = getComputedStyle(document.getElementById('p'));
                const q = getComputedStyle(document.getElementById('q'));
                return {bg: p.backgroundImage, pad: p.padding,
                        radius: p.borderTopLeftRadius, shadow: p.boxShadow,
                        plain: q.backgroundImage};
            }""")
            br.close()
        check('the panel renders the wash', 'linear-gradient' in m['bg'],
              m['bg'][:52])
        check('  with the model screen\'s padding and radius',
              m['pad'] == '20px 24px' and m['radius'] == '12px',
              '%s / %s' % (m['pad'], m['radius']))
        check('  and its softer shadow', '0.06' in m['shadow'],
              m['shadow'][:44])
        check('CONTROL: a plain div gets none of it', m['plain'] == 'none',
              m['plain'][:30])
    except Exception as e:
        for n in ('the panel renders the wash', 'CONTROL: a plain div gets '
                  'none of it'):
            skip(n, 'the browser would not run: %s' % str(e)[:40])

# ---------------------------------------------------------------------- 5
head('5. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    check('this suite is on the gate', ME in read(PS1), ME)

# ---------------------------------------------------------------------- 6
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
print('  NOT PROVED HERE: that the fields inside the panel are grouped')
print('  well. Each swept screen has ONE panel around everything. The')
print('  model screen has three, titled, and splitting the rest that way')
print('  is design work per page rather than a sweep.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
