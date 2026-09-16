"""Show-FormComponents.py - what the entry screens say about fields,
   controls and panels today, and how much of it they say twice.

    python Show-FormComponents.py

READ-ONLY. It writes nothing and changes nothing. Run it from the repo
root. It exists because the build sandbox holds 97 of this repo's 144
templates, and five times now a number derived from that subset has been
wrong - so the numbers §2.L-b is decided on should be yours, not mine.

WHAT IT IS LOOKING FOR

  The heading round found the same thing twice: base reached a class NAME
  but not its RULE, so thirty pages derived the rule by hand and five got
  it wrong. Read as thirty declarations that looks like improvisation.
  Read as one rule it is a standard nobody wrote down.

  This asks whether the fields and panels are in that state. For each
  property it prints the values in use and how many pages use each, so a
  split reads as a split and agreement reads as agreement.

WHAT IT DELIBERATELY DOES NOT DO

  It draws no conclusion and names no winner. A majority is not a
  standard - the label round went against a 338-to-207 majority on
  purpose. The counts are evidence for a decision, not the decision.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This prints text read out of the templates, and some of it is not ASCII.
# On Windows a pipe is not a UTF-8 console, so cp1252 is what Python
# writes, and a character it cannot encode raises rather than printing.
# A crash tells you less than a failure and blocks just as hard.
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

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

MODEL = 'customer_invoice_form.html'

# The properties worth comparing. Anything else is noise at this stage.
WATCH = ('background', 'border', 'border-radius', 'padding', 'margin-bottom',
         'box-shadow', 'font-size', 'font-weight', 'color', 'gap',
         'border-color', 'display', 'transition')


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def pages():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if any(t in rel for t in RECIPE):
                continue
            out.append((rel, os.path.join(dirpath, n)))
    return sorted(out)


def sheets(text):
    """Page-local CSS with comments blanked, the media context kept.

    Yields (selector, declarations, media) - media being the query text a
    rule sits inside, or '' at the top level. A rule's query matters: a
    max-width query with no `screen` keyword fires on PAPER as well, which
    is how printed reports come out phone-sized.
    """
    for css in re.findall(r'<style[^>]*>(.*?)</style>', text, re.S):
        css = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css,
                     flags=re.S)
        stack = []
        i = 0
        while i < len(css):
            at = css.find('@media', i)
            brace = css.find('{', i)
            if brace < 0:
                break
            if 0 <= at < brace:
                q = ' '.join(css[at + 6:brace].split())
                depth, j = 1, brace + 1
                while j < len(css) and depth:
                    if css[j] == '{':
                        depth += 1
                    elif css[j] == '}':
                        depth -= 1
                    j += 1
                stack.append((q, css[brace + 1:j - 1]))
                i = j
                continue
            close = css.find('}', brace)
            if close < 0:
                break
            yield (' '.join(css[i:brace].split()), css[brace + 1:close], '')
            i = close + 1
        for q, body in stack:
            for m in re.finditer(r'([^{}]*)\{([^}]*)\}', body):
                yield (' '.join(m.group(1).split()), m.group(2), q)


def decls(text):
    out = []
    for d in text.split(';'):
        if ':' in d:
            k, v = d.split(':', 1)
            out.append((k.strip().lower(), ' '.join(v.split())))
    return out


def table(title, agg, npages):
    print('')
    print('  %s  - %d page(s) declare it' % (title, npages))
    if not agg:
        print('      nothing')
        return
    for k in sorted(agg, key=lambda k: -sum(agg[k].values())):
        c = agg[k]
        vals = '   '.join('%s (%d)' % (v, n) for v, n in c.most_common(4))
        more = '' if len(c) <= 4 else '   +%d more' % (len(c) - 4)
        flag = '' if len(c) == 1 else '   <- %d spellings' % len(c)
        print('      %-15s %s%s%s' % (k, vals, more, flag))


def head(t):
    print('')
    print('=' * 74)
    print(' ' + t)
    print('=' * 74)


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

ALL = pages()

# ---------------------------------------------------------------- 1
head('1. WHICH PAGES ARE ENTRY SCREENS')

entry, uses_ctrl = [], []
for rel, path in ALL:
    t = read(path)
    if 'form-control' not in t:
        continue
    uses_ctrl.append(rel)
    if re.search(r'<form\b', t):
        entry.append(rel)

print('  %d template(s) in property management.' % len(ALL))
print('  %d use form-control; %d of those carry a <form>.'
      % (len(uses_ctrl), len(entry)))

outside = []
for rel, path in ALL:
    t = read(path)
    if 'form-control' not in t:
        continue
    spans = [m.span() for m in re.finditer(r'<form\b.*?</form>', t, re.S)]
    n = out = 0
    for m in re.finditer(r'class="[^"]*\bform-control\b', t):
        n += 1
        if not any(a <= m.start() < b for a, b in spans):
            out += 1
    if out:
        outside.append((rel, out, n))
tot_out = sum(o for _r, o, _n in outside)
print('  %d control(s) sit OUTSIDE any form - filters, modals, report'
      % tot_out)
print('  pickers. THIS IS THE BLAST RADIUS if base takes .form-control over:')
for rel, o, n in sorted(outside, key=lambda x: -x[1])[:12]:
    print('      %-46s %3d of %3d' % (rel[:46], o, n))
if len(outside) > 12:
    print('      ... and %d more page(s)' % (len(outside) - 12))

# ---------------------------------------------------------------- 2
head('2. THE CONTROL - .form-control, declared page by page')

bare = collections.defaultdict(collections.Counter)
comp = collections.defaultdict(collections.Counter)
nb = nc = 0
focus = collections.Counter()
phone_ctrl = collections.Counter()
for rel, path in ALL:
    seen_b = seen_c = False
    for sel, body, media in sheets(read(path)):
        if 'form-control' not in sel and 'line-input' not in sel:
            continue
        if ':focus' in sel:
            for k, v in decls(body):
                if k == 'border-color':
                    focus[v] += 1
            continue
        if media:
            for k, v in decls(body):
                if k == 'font-size':
                    phone_ctrl['%s  in  @media %s' % (v, media)] += 1
            continue
        target = None
        if re.fullmatch(r'\.form-control', sel):
            target, seen_b = bare, True
        elif re.search(r'(?<![-\w])\.form-control\b', sel):
            target, seen_c = comp, True
        if target is None:
            continue
        for k, v in decls(body):
            if k in WATCH:
                target[k][v] += 1
    nb += seen_b
    nc += seen_c

table('A BARE .form-control rule', bare, nb)
table('A COMPOUND rule reaching .form-control', comp, nc)
print('')
print('  :focus border-color - %d rule(s)' % sum(focus.values()))
for v, n in focus.most_common():
    print('      %-30s %d' % (v, n))
print('')
print('  the control font-size inside a media query (16px stops iOS zooming')
print('  the page on tap; a query with no `screen` also fires on PAPER):')
for v, n in phone_ctrl.most_common(8):
    print('      %-58s %d' % (v[:58], n))

# ---------------------------------------------------------------- 3
head('3. THE FIELD - .form-group, its label and its help text')

grp = collections.defaultdict(collections.Counter)
lbl = collections.defaultdict(collections.Counter)
hlp = collections.defaultdict(collections.Counter)
ng = nl = nh = 0
for rel, path in ALL:
    sg = sl = sh = False
    for sel, body, media in sheets(read(path)):
        if media:
            continue
        d = [(k, v) for k, v in decls(body) if k in WATCH]
        if re.search(r'(?<![-\w])\.form-(group|field)\b', sel) \
                and not re.search(r'\blabel\b', sel):
            sg = True
            for k, v in d:
                grp[k][v] += 1
        if re.search(r'\blabel\b(?![-\w])', sel) and 'form' in sel:
            sl = True
            for k, v in d:
                lbl[k][v] += 1
        if re.search(r'(?<![-\w])\.form-text\b', sel) or 'text-muted' in sel:
            sh = True
            for k, v in d:
                hlp[k][v] += 1
    ng += sg
    nl += sl
    nh += sh

table('THE FIELD WRAPPER', grp, ng)
table('THE LABEL', lbl, nl)
table('THE HELP TEXT', hlp, nh)

# ---------------------------------------------------------------- 4
head('4. THE PANEL - the box a group of fields sits in')

PANEL = re.compile(r'(?<![-\w])\.(form-card|cust-panel|form-panel|form-section'
                   r'|form-container|form-wrapper|card-panel|filter-card)'
                   r'(?![-\w])')
pan = collections.defaultdict(collections.Counter)
titles = collections.defaultdict(collections.Counter)
which = collections.Counter()
np_ = nt = 0
for rel, path in ALL:
    sp = st = False
    for sel, body, media in sheets(read(path)):
        if media:
            continue
        m = PANEL.search(sel)
        if not m:
            continue
        d = [(k, v) for k, v in decls(body) if k in WATCH]
        if re.search(r'title|heading', sel):
            st = True
            for k, v in d:
                titles[k][v] += 1
        elif sel == m.group(0):
            sp = True
            which[m.group(0)] += 1
            for k, v in d:
                pan[k][v] += 1
    np_ += sp
    nt += st

print('  the names in use:')
for k, n in which.most_common():
    print('      %-20s %d page(s)' % (k, n))
table('THE PANEL BOX', pan, np_)
table('THE PANEL TITLE', titles, nt)

# ---------------------------------------------------------------- 5
head('5. THE ROW - how two fields sit side by side')

row = collections.Counter()
cols = collections.Counter()
for rel, path in ALL:
    t = read(path)
    if re.search(r'class="[^"]*\bform-row\b', t):
        row['markup: form-row'] += 1
    if re.search(r'class="[^"]*\brow\b[^"]*"', t):
        row['markup: row'] += 1
    for c in re.findall(r'class="[^"]*\b(col-(?:md-|sm-|lg-)?\d+)\b', t):
        cols[c] += 1
    for sel, body, media in sheets(t):
        if media:
            continue
        if re.fullmatch(r'\.form-row', sel):
            row['page redefines .form-row'] += 1
        if re.match(r'\.col-\d', sel):
            row['page redefines a .col-* width'] += 1
for k, n in row.most_common():
    print('  %-32s %d page(s)' % (k, n))
print('')
print('  the column classes in the markup:')
for k, n in cols.most_common(10):
    print('      %-14s %d use(s)' % (k, n))

# ---------------------------------------------------------------- 6
head('6. HOW FAR EACH ENTRY SCREEN IS FROM THE MODEL PAGE')

model = os.path.join(T, MODEL)
if not os.path.exists(model):
    print('  %s not found.' % MODEL)
else:
    want = {}
    for sel, body, media in sheets(read(model)):
        if media:
            continue
        if sel in ('.form-control', '.form-group', '.cust-panel',
                   '.panel-title', '.form-row'):
            want[sel] = dict(decls(body))
    print('  The model page declares:')
    for sel in sorted(want):
        print('      %s' % sel)
        for k in sorted(want[sel]):
            print('          %-16s %s' % (k, want[sel][k]))
    print('')
    print('  Pages whose bare .form-control matches the model exactly:')
    same = []
    for rel, path in ALL:
        if rel == MODEL:
            continue
        for sel, body, media in sheets(read(path)):
            if media or not re.fullmatch(r'\.form-control', sel):
                continue
            d = dict(decls(body))
            if all(d.get(k) == v for k, v in want.get('.form-control', {}).items()):
                same.append(rel)
    print('      %d of %d' % (len(same), len(entry)))
    for r in same[:10]:
        print('          %s' % r)

# ---------------------------------------------------------------- 7
head('7. WHAT THIS ADDS UP TO')

print('  Every number above is a count of pages that WROTE A RULE OUT.')
print('  Where a property shows one spelling, the system already agrees and')
print('  base can simply say it. Where it shows several, somebody has to')
print('  choose - and the majority is evidence, not the answer.')
print('')
print('  Nothing was written. This script only reads.')
