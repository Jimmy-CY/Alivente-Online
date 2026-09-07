#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Show-RequiredMarkers.py - how many ways does this system say "required"?

    python Show-RequiredMarkers.py            the property side
    python Show-RequiredMarkers.py --recipes  include the recipe / meal side
    python Show-RequiredMarkers.py --full <template>   one file, in detail
    python Show-RequiredMarkers.py --dead     only the rules nothing renders
    python Show-RequiredMarkers.py --strict   exit 1 while >1 spelling remains

READ ONLY: writes nothing, opens nothing for editing.

WHY THIS EXISTS. A round was about to fix ten inline `style="color: red"`
asterisks on the Projects forms. Scanning first turned ten sites into a
system-wide finding: the same idea is spelled six different ways across forty
templates, three quarters of them leaning on BOOTSTRAP rather than on
anything of ours, and base defines no required-marker at all.

WHAT IT REPORTS, AND WHY EACH COLUMN IS HERE

  SPELLING    the exact shape of the marker: the class list on the span that
              holds the asterisk, `(inline)` when it carries a style
              attribute instead, or `(bare)` when the asterisk sits loose in
              the label with no element of its own.

  SITES       how many labels use it, and in how many templates.

  RULE        whether the page or base actually DEFINES that class.
              Three answers and they mean different things:

                base    base.html styles it - the only sustainable answer
                page    the template styles it locally
                BOOT    it is a Bootstrap class and Bootstrap styles it -
                        which works, and means the system's error colour is
                        Bootstrap's #dc3545 rather than --alv-bad
                NONE    nothing styles it anywhere. The asterisk renders as
                        ordinary body text, and the "required" signal is a
                        character rather than a colour.

  DEAD        classes DECLARED in a stylesheet that no label carries. Round D
              found six of these in two files and one of them was a #FF0000
              somebody was about to redesign. Before changing a rule, check
              anything renders it.

WHAT IT DELIBERATELY DOES NOT DO. It does not tell you which spelling should
win. That is a decision, and it needs the rendered comparison this tool's
output is meant to size - not a majority vote. `text-danger` has the most
sites and is the one spelling that belongs to somebody else.

TWO THINGS TO BE CAREFUL OF, both learned the hard way in this project.

  A SUBSTRING TEST CATCHES EVERY SUPERSTRING. `required` is inside
  `required-mark` and `required-marker`; `req` is inside both. Everything
  here works on class TOKENS, never on `in`.

  A COMMENT STRIPPER THAT DOES NOT KNOW WHAT A SCHEME IS EATS EVERY URL.
  `//` opens a JavaScript comment and also sits inside every `https://`.
  Whole-line comments only.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

RECIPE = ('recipe', 'meal_plan', 'meal_plans', 'ingredient', 'wcim',
          'celebration', 'pantry', 'unit_conversions', 'measurement_units',
          'household_member', 'map_ingredients', 'import_recipe',
          'preview_imported')

# Bootstrap ships these; they work, and they are not ours.
BOOTSTRAP = {'text-danger', 'text-muted', 'text-warning', 'text-info',
             'text-primary', 'text-secondary', 'text-success'}


def is_recipe_side(f):
    return any(k in f for k in RECIPE)


def templates(include_recipes):
    out = []
    for base_dir, _d, files in os.walk(TPL):
        for fn in sorted(files):
            if not fn.endswith('.html') or '.bak_' in fn:
                continue
            rel = os.path.relpath(os.path.join(base_dir, fn),
                                  TPL).replace(os.sep, '/')
            if include_recipes or not is_recipe_side(rel):
                out.append(rel)
    return sorted(out)


def read(rel):
    p = os.path.join(TPL, *rel.split('/'))
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(src):
    c = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
    return re.sub(r'/\*.*?\*/', '', c, flags=re.S)


def markup_of(src):
    src = re.sub(r'<!--.*?-->', '', src, flags=re.S)
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', src, flags=re.S)


def selectors(css):
    """Every class token that appears in a selector position."""
    out = set()
    for sel, _ in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        if sel.strip().startswith('@'):
            continue
        out.update(re.findall(r'\.([A-Za-z][\w-]*)', sel))
    return out


# ---------------------------------------------------------------------------
# find the markers
# ---------------------------------------------------------------------------
# A required marker is an asterisk inside a <label>. Everything else about it
# - a span, a class, an inline style, nothing at all - is the variation this
# tool exists to count.
LABEL = re.compile(r'<label\b[^>]*>(.*?)</label>', re.S)
SPAN_STAR = re.compile(r'<span([^>]*)>\s*\*\s*</span>')


# ---------------------------------------------------------------------------
# WHAT COUNTS AS A BARE ASTERISK - and the bug that made this a rule of its own
# ---------------------------------------------------------------------------
# The first draft matched any `*` in a label body that was not already in a
# span. Three of the four "bare markers" it found were not markers at all:
# they were the `*` inside `accept="image/*"` on a file input nested in the
# label. The patcher wrapped it, producing
#
#     accept="image/<span class="alv-req">*</span>"
#
# which breaks the attribute AND the file picker's filter. Caught by reading
# what the four actually were, which is the only reason it was caught: the
# SCANNER had the same bug, so the patcher's cross-check against it passed.
#
# TWO IMPLEMENTATIONS OF ONE RULE DO NOT DRIFT - BUT ONE WRONG RULE
# IMPLEMENTED TWICE IS STILL WRONG. A cross-check between two tools that
# share a definition tests agreement, not correctness.
#
# So: an asterisk only counts when it is TEXT. Tags are blanked first, which
# puts every attribute value out of reach.
def text_only(body):
    """The label body with every tag blanked to spaces, offsets preserved."""
    return re.sub(r'<[^>]*>', lambda m: ' ' * len(m.group(0)), body)


def bare_star_at(body):
    """Offset of a bare asterisk in the label's TEXT, or None."""
    t = text_only(body)
    m = re.search(r'\*', t)
    return m.start() if m else None


def spelling_of(label_body):
    """The marker's shape, or None if this label has no asterisk."""
    if '*' not in label_body:
        return None
    m = SPAN_STAR.search(label_body)
    if not m:
        # ONLY a bare asterisk in TEXT. `accept="image/*"` on a nested file
        # input is not a required marker, and the first draft counted three
        # of them.
        return '(bare)' if bare_star_at(label_body) is not None else None
    attrs = m.group(1)
    cm = re.search(r'class="([^"]*)"', attrs)
    if cm and cm.group(1).strip():
        return ' '.join(sorted(cm.group(1).split()))
    if re.search(r'style="[^"]*"', attrs):
        sm = re.search(r'style="([^"]*)"', attrs)
        return '(inline) ' + ' '.join(sm.group(1).split())
    return '(span, no class)'


BASE_CSS = css_of(read('base.html')) if os.path.exists(
    os.path.join(TPL, 'base.html')) else ''
BASE_SELS = selectors(BASE_CSS)

INCLUDE = '--recipes' in sys.argv
FILES = templates(INCLUDE)

sites = {}          # spelling -> [(template, label text)]
per_file = {}       # template -> {spelling: n}
declared = {}       # template -> set of marker-ish classes its CSS defines
used = {}           # template -> set of marker classes its markup carries

for rel in FILES:
    src = read(rel)
    mk, cs = markup_of(src), css_of(src)
    per_file[rel] = {}
    declared[rel] = set()
    used[rel] = set()
    for sel in selectors(cs):
        # NOT a loose `mark`: that caught .cf-breakeven-mark, a chart
        # annotation on the cashflow forecast, and reported it as a dead
        # required marker. A substring test catches every superstring, and a
        # LOOSE one catches things that were never in the family.
        if re.fullmatch(r'required|required-mark|required-marker|req', sel,
                        re.I):
            declared[rel].add(sel)
    for m in LABEL.finditer(mk):
        sp = spelling_of(m.group(1))
        if sp is None:
            continue
        txt = ' '.join(re.sub(r'<[^>]+>', ' ', m.group(1)).split())[:44]
        sites.setdefault(sp, []).append((rel, txt))
        per_file[rel][sp] = per_file[rel].get(sp, 0) + 1
        if not sp.startswith('('):
            used[rel].update(sp.split())


# WHAT IT PAINTS, which is the column that turns a list of names into a
# finding. Bootstrap's own value is read from the test fixture when it is
# present rather than remembered, and base's from base.html.
BOOT_CSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
_boot = ''
if os.path.exists(BOOT_CSS):
    with open(BOOT_CSS, encoding='utf-8', errors='replace') as _fh:
        _boot = _fh.read()


def _lookup(css, cls):
    """The `color` a stylesheet gives a class, if any."""
    for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        if not re.search(r'\.' + re.escape(cls) + r'(?![\w-])', sel):
            continue
        m = re.search(r'(?<![\w-])color\s*:\s*([^;!}]+)', body)
        if m:
            return m.group(1).strip()
    return None


def paints(sp, rel):
    """What this spelling actually renders as, and where that came from."""
    if sp.startswith('(inline)'):
        m = re.search(r'color:\s*([^;]+)', sp)
        return (m.group(1).strip() if m else '?'), 'inline'
    if sp.startswith('('):
        return 'inherit', 'nothing'
    for cls in sp.split():
        v = _lookup(BASE_CSS, cls)
        if v:
            return v, 'base'
        v = _lookup(css_of(read(rel)), cls)
        if v:
            return v, 'page'
        if _boot:
            v = _lookup(_boot, cls)
            if v:
                return v, 'bootstrap'
    return 'inherit', 'nothing'


def where_styled(cls, rel):
    if cls in BASE_SELS:
        return 'base'
    if cls in selectors(css_of(read(rel))):
        return 'page'
    if cls in BOOTSTRAP:
        return 'BOOT'
    return 'NONE'


# ---------------------------------------------------------------------------
# --full: one template, every site
# ---------------------------------------------------------------------------
if '--full' in sys.argv:
    i = sys.argv.index('--full')
    if i + 1 >= len(sys.argv):
        sys.exit('! --full needs a template name')
    want = sys.argv[i + 1]
    hits = [(sp, r, t) for sp, lst in sites.items() for r, t in lst
            if r == want or r.endswith('/' + want)]
    if not hits:
        sys.exit('! no required markers found in %s' % want)
    print('\n  %s\n' % want)
    for sp, r, t in sorted(hits):
        print('    %-28s %s' % (sp[:28], t))
    print('\n  its stylesheet declares: %s'
          % (', '.join(sorted(declared.get(want, []))) or 'nothing'))
    sys.exit(0)

# ---------------------------------------------------------------------------
# the table
# ---------------------------------------------------------------------------
print()
print('  REQUIRED-FIELD MARKERS - one idea, %d spellings' % len(sites))
print('  An asterisk inside a <label>. Everything else about it varies.')
print()
print('  %-30s %6s %6s  %-5s %-9s %s'
      % ('SPELLING', 'SITES', 'FILES', 'RULE', 'PAINTS', 'from'))
print('  ' + '-' * 92)

order = sorted(sites.items(), key=lambda kv: -len(kv[1]))
_by = {}
tot_sites = tot_files = 0
for sp, lst in order:
    fs = sorted(set(r for r, _ in lst))
    tot_sites += len(lst)
    if sp.startswith('('):
        rule = '-'
    else:
        toks = sp.split()
        marks = [where_styled(c, fs[0]) for c in toks]
        rule = ('base' if 'base' in marks else
                'page' if 'page' in marks else
                'BOOT' if 'BOOT' in marks else 'NONE')
    _col, _src = paints(sp, fs[0])
    _by.setdefault(_col.lower(), []).append((sp, len(lst)))
    print('  %-30s %6d %6d  %-5s %-9s %s'
          % (sp[:30], len(lst), len(fs), rule, _col[:9], _src))
tot_files = len(set(r for lst in sites.values() for r, _ in lst))
print('  ' + '-' * 92)
print('  %d site(s) across %d template(s).' % (tot_sites, tot_files))
print()

# ---------------------------------------------------------------------------
# what nothing renders
# ---------------------------------------------------------------------------
dead = []
for rel in FILES:
    for cls in sorted(declared[rel]):
        if cls not in used[rel]:
            # a class may be declared here and worn on another page
            worn = any(cls in used[o] for o in FILES if o != rel)
            dead.append((rel, cls, 'worn elsewhere' if worn else 'NOWHERE'))
if dead:
    print('  DECLARED BUT NOT WORN ON THAT PAGE')
    print('  Round D found six of these, and one was a #FF0000 about to be')
    print('  redesigned. Before changing a rule, check anything renders it.')
    print()
    for rel, cls, note in dead:
        print('    %-42s .%-18s %s' % (rel[:42], cls[:18], note))
    print()

if '--dead' in sys.argv:
    sys.exit(0)

# ---------------------------------------------------------------------------
# reach
# ---------------------------------------------------------------------------
mixed = {r: v for r, v in per_file.items() if len(v) > 1}
if mixed:
    print('  TEMPLATES THAT USE MORE THAN ONE SPELLING - %d of them'
          % len(mixed))
    print('  These are the ones where the inconsistency is visible on a')
    print('  single screen rather than only across the system.')
    print()
    for r, v in sorted(mixed.items()):
        print('    %-42s %s' % (r[:42],
                                ', '.join('%s x%d' % (k[:22], n)
                                          for k, n in sorted(v.items()))))
    print()

print('  WHAT THEY ACTUALLY PAINT - %d distinct outcome(s) behind %d '
      'spellings' % (len(_by), len(sites)))
for _c, _v in sorted(_by.items(), key=lambda kv: -sum(n for _, n in kv[1])):
    print('    %-10s %4d site(s)   via %s'
          % (_c, sum(n for _, n in _v), ', '.join(s for s, _ in _v)))
_alv = re.search(r'--alv-bad:\s*(#[0-9a-fA-F]{3,8})', BASE_CSS)
if _alv:
    print()
    print("    base's own danger colour is %s, and NONE of the %d sites uses"
          % (_alv.group(1), tot_sites))
    print('    it. The system says "required" in a colour it does not own.')
print()
print('  BASE DEFINES A REQUIRED MARKER: %s'
      % ('yes' if any(re.search(r'require', s, re.I) for s in BASE_SELS)
         else 'NO - which is why there are %d spellings' % len(sites)))
print()
print('  RULE  base = base.html styles it | page = the template does')
print('        BOOT = a Bootstrap class, so the error colour is Bootstrap\'s')
print('             #dc3545 rather than --alv-bad')
print('        NONE = nothing styles it. The asterisk is body text, and the')
print('             signal is a character rather than a colour.')
print()
print('  This tool does NOT say which spelling should win. That needs the')
print('  rendered comparison it is meant to size, not a majority vote - and')
print('  the largest group is the one that belongs to Bootstrap.')
print()

if '--strict' in sys.argv and len(sites) > 1:
    sys.exit(1)
sys.exit(0)
