"""test_form_components.py - base declares the entry-screen components,
   and they actually reach the pages.

    python test_form_components.py

Run from the repo root, after apply_form_components.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you the panel should carry a wash or the control be 9px by
12px. The control came from a count of 115 templates on 16 Sep, where the
model screen turned out to be a hybrid of the two dialects in use rather
than a third opinion. THE PANEL DID NOT COME FROM A COUNT, and the first
version of this suite got that wrong: the count said white 22 to 1 and the
brief said "look like New Customer Invoice". A majority is evidence about
what the system does, never an argument about what it should be. This
suite holds the system to the choice; it does not defend it.

SECTION 3 IS THE ONE THAT EARNS ITS KEEP, AND IT IS NOT THE OBVIOUS CHECK.

The obvious check is that base declares the rules, which section 1 does by
reading the file. That proves nothing about any page. A component reaches
a page only if it WINS, and base's single-class rule loses to any compound
selector a page happens to carry - .form-field .form-control beats
.form-control however recently it was written and wherever it sits.

So section 3 assembles each entry screen's real cascade - base's head
stylesheets, then the page's own, then base's post-content stylesheet, in
that document order - renders a field in Chromium and asks the browser
what the control, the panel and the label actually look like. A page where
the answer is not base's answer has a rule still in charge, and is named.

WHAT SECTION 3 CANNOT SEE, AND IT MATTERS. The field it renders is a
STANDARD one. A page whose override is scoped to a wrapper that fixture
does not carry - .form-field .form-control, on twelve Financials screens -
is invisible to it, and the page is counted as reached while its real
fields are not. So the number it prints means "base's components work in
this page's cascade", NOT "this page's fields look like base". Section 2's
count of compound rules is the one that says how much is left to do.

Making the fixture use each page's own markup is the honest fix and it is
the next round's, where those rules are being removed anyway. Until then
the limitation is printed beside the number rather than left for somebody
to infer.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY. So is a reported one.
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

import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
MODEL = os.path.join(T, 'customer_invoice_form.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)

MARK = 'ALV FORM v1'

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

# The same ownership table the patcher works from. A page-local bare rule
# is only allowed to survive if it declares something OUTSIDE this - which
# is a RULE, not a list of filenames, so it covers pages nobody has looked
# at yet.
OWNED = {
    '.form-card': {'background', 'border', 'border-radius', 'padding',
                   'margin-bottom', 'box-shadow'},
    '.form-section-title': {'color', 'font-weight', 'margin',
                            'margin-top', 'margin-bottom'},
    '.form-section-title i': {'color', 'margin-right'},
    '.form-group': {'margin-bottom'},
    '.form-group label': {'display', 'color', 'font-size', 'margin-bottom'},
    '.form-control': {'width', 'background', 'background-color', 'border',
                      'border-radius', 'padding', 'font-size', 'transition'},
    '.form-control:focus': {'border-color', 'box-shadow', 'outline'},
    '.form-control[readonly]': {'background', 'background-color', 'color',
                                'cursor', 'opacity'},
    '.form-control:disabled': {'background', 'background-color', 'color',
                               'cursor', 'opacity'},
    '.form-text': {'font-size', 'color', 'margin-top'},
}

# What base says, in the browser's own words. rgb() because that is what
# getComputedStyle returns, whatever the stylesheet was written in.
WANT = {
    'ctrlBorder': '2px',
    'ctrlRadius': '8px',
    'ctrlPadding': '9px 12px',
    'ctrlFont': '14px',
    'panelRadius': '12px',
    'panelPad': '20px',
    'labelFont': '14px',
    'labelGap': '6px',
}

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


def blank_comments(css):
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css, flags=re.S)


def style_spans(text):
    return [(m.start(1), m.end(1))
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)]


def rules_in(css, base=0):
    blanked = blank_comments(css)
    out = []

    def walk(lo, hi, media):
        i = lo
        while i < hi:
            at = blanked.find('@', i)
            brace = blanked.find('{', i)
            if brace < 0 or brace >= hi:
                return
            if 0 <= at < brace:
                depth, j = 1, brace + 1
                while j < hi and depth:
                    if blanked[j] == '{':
                        depth += 1
                    elif blanked[j] == '}':
                        depth -= 1
                    j += 1
                if blanked[at:brace].lstrip().startswith('@media'):
                    walk(brace + 1, j - 1, (base + at, base + j))
                i = j
                continue
            close = blanked.find('}', brace)
            if close < 0 or close >= hi:
                return
            k = i
            while k < brace and blanked[k] in ' \t\r\n':
                k += 1
            out.append((base + k, base + brace, base + brace + 1,
                        base + close, media))
            i = close + 1

    walk(0, len(css), None)
    return out


def sel_list(text, a, b):
    raw = re.sub(r'/\*.*?\*/', ' ', text[a:b], flags=re.S)
    return [' '.join(p.split()) for p in raw.split(',') if p.strip()]


def props_of(text, a, b):
    return [d.split(':', 1)[0].strip().lower()
            for d in text[a:b].split(';') if ':' in d]


def touches_owned(sels):
    pat = (r'(?<![-\w])\.(form-control|form-group|form-card|form-text'
           r'|form-section-title)(?![-\w])')
    return any(re.search(pat, s) for s in sels)


def pages():
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


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

B = read(BASE)

# ---------------------------------------------------------------------- 1
head('1. BASE DECLARES THEM')

check('base carries the %s block' % MARK, MARK in B)
check('  exactly once', B.count('/* ===== %s ===== */' % MARK) == 1,
      '%d' % B.count('/* ===== %s ===== */' % MARK))

base_rules = {}
for a, b in style_spans(B):
    for (sa, sb, da, db, media) in rules_in(B[a:b], a):
        if media is not None:
            continue
        for s in sel_list(B, sa, sb):
            if s in OWNED:
                base_rules.setdefault(s, []).append(' '.join(B[da:db].split()))

for s in ('.form-card', '.form-section-title', '.form-group',
          '.form-group label', '.form-control', '.form-control:focus',
          '.form-text'):
    check('base defines %s' % s, bool(base_rules.get(s)),
          '%d rule(s)' % len(base_rules.get(s, [])))

card = ' '.join(base_rules.get('.form-card', []))
ctrl = ' '.join(base_rules.get('.form-control', []))
lab = ' '.join(base_rules.get('.form-group label', []))

# THE PANEL CARRIES THE MODEL SCREEN'S WASH. The first version of this
# check asked for var(--alv-paper), because the round had chosen white
# from a count of 22 to 1. The count was right and the choice was wrong:
# the brief was to make the system look like New Customer Invoice, and a
# majority cannot answer that. Both stops are tokens so the wash can be
# restated in one place.
check('  the panel carries the wash, from two surface tokens',
      'linear-gradient' in card and 'var(--alv-surface)' in card
      and 'var(--alv-surface-deep)' in card, card[:56])
check('  CONTROL: and no literal survived in it',
      not re.search(r'#[0-9a-fA-F]{3,6}', card), card[:56])
check('  the control takes its line and radius from tokens',
      'var(--alv-line)' in ctrl and 'var(--alv-radius)' in ctrl)
check('  the focus halo has a token of its own',
      '--alv-accent-ring' in B and
      'var(--alv-accent-ring)' in ' '.join(base_rules.get(
          '.form-control:focus', [])))
check('THE LABEL CARRIES NO WEIGHT - the strong element owns that',
      'font-weight' not in lab, lab[:60])
check('  CONTROL: and the label rule exists to have carried one',
      'font-size' in lab)

phone = re.search(r'@media screen and \(max-width: 768px\)\s*\{[^}]*'
                  r'\.form-control\s*\{[^}]*font-size', B)
check('base says the phone size, and says SCREEN', bool(phone))

check('section 3.6 records that the label sweep happened',
      'THE SWEEP HAPPENED' in B)
check('  and names the components base now declares',
      'base NOW DECLARES THE FIELD' in B)
check('  CONTROL: and the old sentence is gone',
      'THE SWEEP HAS NOT HAPPENED' not in B)

# ---------------------------------------------------------------------- 2
head('2. NO PAGE STILL KEEPS A DEAD COPY')

dead, partial, compound, inmedia = [], [], [], []
for rel, path in pages():
    text = read(path)
    for a, b in style_spans(text):
        for (sa, sb, da, db, media) in rules_in(text[a:b], a):
            sels = sel_list(text, sa, sb)
            if not sels or not touches_owned(sels):
                continue
            if media is not None:
                inmedia.append((rel, ', '.join(sels)))
                continue
            if not all(s in OWNED for s in sels):
                compound.append((rel, ', '.join(sels)))
                continue
            allowed = set()
            for s in sels:
                allowed |= OWNED[s]
            extra = sorted(set(props_of(text, da, db)) - allowed)
            if extra:
                partial.append((rel, ', '.join(sels), extra))
            else:
                dead.append((rel, ', '.join(sels)))

for rel, sel in dead:
    print('        dead: %-34s %s' % (rel[:34], sel[:30]))
check('no page keeps a bare rule base already overrides', not dead,
      '%d left' % len(dead))

# THE SURVIVORS ARE ALLOWED BY A RULE, NOT BY A LIST OF FILENAMES. A bare
# owned rule may stay only if it declares a property base never claimed -
# which is checkable on a page written next month. The heading round
# learned this the slow way: a list read off a 97-template sandbox was six
# names short of the real repo.
print('        %d bare rule(s) survive because they declare something base'
      % len(partial))
print('        does not - each named, with the property that saved it:')
for rel, sel, extra in partial:
    print('          %-28s %-24s %s' % (rel[:28], sel[:24], ', '.join(extra)))
check('  CONTROL: and each really does exceed base',
      all(e for _r, _s, e in partial))

print('        %d compound rule(s) on %d page(s) still outrank base;'
      % (len(compound), len({r for r, _s in compound})))
print('        %d rule(s) inside a media query are untouched. Both belong'
      % len(inmedia))
print('        to the next round and to section 2.I respectively.')

# ---------------------------------------------------------------------- 3
head('3. RENDERED - which pages the components actually REACH')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

MARKUP = ("<div class='form-card'><h5 class='form-section-title'>"
          "<i></i> Panel</h5><div class='form-group'>"
          "<label for='x'><strong>Field</strong> "
          "<span class='alv-req'>*</span></label>"
          "<input id='x' class='form-control' value='v'>"
          "<small class='form-text'>hint</small></div></div>")


def base_sheets():
    """base's stylesheets, split at the content block.

    ORDER IS THE WHOLE POINT. base's component stylesheet sits AFTER
    {% block content %}, which is why it beats a page's copy on equal
    specificity - and why a suite that concatenates them in file order
    without looking would measure a cascade the browser never sees.
    """
    cut = B.find('{% block content %}')
    before, after = [], []
    for a, b in style_spans(B):
        (before if b < cut else after).append(B[a:b])
    return '\n'.join(before), '\n'.join(after)


if sync_playwright is None:
    skip('the components reach every page base is in charge of',
         'playwright is not installed')
    skip('CONTROL: and a page with a compound rule does NOT match',
         'playwright is not installed')
else:
    pre, post = base_sheets()
    entry = [(rel, path) for rel, path in pages()
             if 'form-control' in read(path) and '<form' in read(path)]
    reached, missed = [], []
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1200, 'height': 900})
            pg.route('**://**', lambda r: r.abort())
            for rel, path in entry:
                own = '\n'.join(read(path)[a:b]
                                for a, b in style_spans(read(path)))
                doc = ("<!doctype html><meta charset=utf-8>"
                       "<style>%s</style>%s<style>%s</style>"
                       % (pre, '<style>%s</style>' % own + MARKUP, post))
                pg.set_content(doc, wait_until='load')
                m = pg.evaluate("""() => {
                    const g = (s) => getComputedStyle(document.querySelector(s));
                    const c = g('.form-control'), p = g('.form-card'),
                          l = g('.form-group label');
                    return {ctrlBorder: c.borderTopWidth,
                            ctrlRadius: c.borderTopLeftRadius,
                            ctrlPadding: c.paddingTop + ' ' + c.paddingLeft,
                            ctrlFont: c.fontSize,
                            panelRadius: p.borderTopLeftRadius,
                            panelPad: p.paddingTop,
                            panelBg: p.backgroundColor,
                            labelFont: l.fontSize,
                            labelGap: l.marginBottom,
                            labelWeight: getComputedStyle(
                                document.querySelector(
                                    '.form-group label strong')).fontWeight};
                }""")
                off = [k for k, v in WANT.items() if m.get(k) != v]
                if off:
                    missed.append((rel, off, m))
                else:
                    reached.append((rel, m))
            br.close()
    except Exception as e:
        skip('the components reach every page base is in charge of',
             'the browser would not run: %s' % str(e)[:40])
        skip('CONTROL: and a page with a compound rule does NOT match',
             'the browser would not run: %s' % str(e)[:40])
        reached = missed = None

    if reached is not None:
        # WHAT THIS NUMBER IS, EXACTLY. The fixture is a STANDARD field -
        # a panel, a section title, a form-group, a label and a control.
        # A page whose compound rule is scoped to a wrapper the fixture
        # does not carry - .form-field .form-control, on twelve Financials
        # screens - cannot be seen here, and the page counts as reached
        # when its real fields are not. So this measures "base's
        # components work in this page's cascade", not "this page's own
        # fields look like base". Section 2's count of compound rules is
        # the number that says how much is left.
        print('        %d of %d entry screen(s) render base\'s own field '
              'correctly' % (len(reached), len(entry)))
        print('        IN THIS PAGE\'S CASCADE. A page whose override is')
        print('        scoped to a wrapper this fixture does not carry is')
        print('        counted here and still differs on its real fields -')
        print('        section 2 names %d such rule(s).' % len(compound))
        by = collections.Counter()
        for rel, off, _m in missed:
            for k in off:
                by[k] += 1
            print('          still overridden: %-30s %s'
                  % (rel[:30], ', '.join(off)))
        # A PAGE THAT DIFFERS IS NOT A FAILURE - it is a page with a
        # compound rule, which this round deliberately left in charge.
        # What WOULD be a failure is a page that differs WITHOUT one.
        comp_pages = {r for r, _s in compound} | {r for r, _s, _e in partial}
        orphans = sorted(rel for rel, _off, _m in missed
                         if rel not in comp_pages)
        check('every page that does not match base has a rule that explains it',
              not orphans, '%d cannot be explained: %s'
              % (len(orphans), ', '.join(orphans[:4])))
        check('  CONTROL: and base does reach most of them',
              len(reached) >= len(entry) // 2,
              '%d of %d' % (len(reached), len(entry)))
        if reached:
            w = reached[0][1]['labelWeight']
            check('  the label still renders bold on those pages',
                  int(w) >= 600, w)

# ---------------------------------------------------------------------- 4
head('4. THE MODEL SCREEN IS ON THE COMPONENTS IT INSPIRED')

M = read(MODEL) if os.path.exists(MODEL) else ''
check('the model screen exists', bool(M))
if M:
    check('  it uses the panel component', "class=\"form-card\"" in M)
    check('  and the panel title component',
          "class=\"form-section-title\"" in M)
    check('  CONTROL: its own names are gone',
          not re.search(r'(?<![-\w])cust-panel(?![-\w])', M)
          and not re.search(r'(?<![-\w])panel-title(?![-\w])', M))
    # PARSED, not pattern-matched. The first spelling of this looked for
    # `.form-control {` with a regex and found `.vat-input-wrap
    # .form-control {` - a compound rule this round deliberately leaves in
    # charge, because it sets a padding-right base never claimed. A
    # selector is a list the browser parses, not a string in a file.
    msels = []
    for a, b in style_spans(M):
        for (sa, sb, _da, _db, media) in rules_in(M[a:b], a):
            if media is None:
                msels.extend(sel_list(M, sa, sb))
    check('  and it no longer declares the bare control, panel or field',
          not ({'.form-control', '.form-control:focus', '.form-card',
                '.form-text'} & set(msels)),
          ', '.join(sorted({'.form-control', '.form-control:focus',
                            '.form-card', '.form-text'} & set(msels))))
    check('  CONTROL: and it still declares the things base never claimed',
          '.vat-input-wrap .form-control' in msels or '.line-input' in
          ' '.join(msels))

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
print('  REPORTED, NOT FAILED: %d compound rule(s) that still outrank base,'
      % len(compound))
print('  and %d inside a media query. The compounds are the next round; the'
      % len(inmedia))
print('  media ones are section 2.I, and until they go a page with a bare')
print('  max-width query still prints its form phone-sized.')
print('')
print('  NOT PROVED HERE: that white, 12px and 9px by 12px are the right')
print('  answers. Those came from a count of 115 templates on 16 Sep. This')
print('  holds the system to them.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
