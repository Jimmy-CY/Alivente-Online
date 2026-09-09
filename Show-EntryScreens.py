"""Show-EntryScreens.py - what an Add or Edit screen is actually made of,
   across the whole system.

    python Show-EntryScreens.py            every template
    python Show-EntryScreens.py finance    only paths containing 'finance'

Run from the repo root. READ-ONLY.

WHY IT EXISTS. The next round brings every Add and Edit screen into line with
New Customer Invoice. Two cautions were written down before it started:
MEASURE FIRST, and DRAW THE COMPONENT FROM TWO EXAMPLES, NOT ONE. This is the
measuring.

WHAT COUNTS AS AN ENTRY SCREEN is decided by what the page DOES, not by what
it is called. A page qualifies if it posts a form that carries at least three
data controls. Naming rounds on this codebase have gone wrong twice by
matching filenames: a scanner's exclusion list was name-based and swept a
recipe page by accident, and a survey named after a colour found only that
colour. `customer_form` and `fsr_add` do not say add or edit; `act_expense`
holds an editing mode inside a listing page.

IT WALKS */*.html. Two rounds measured only the top level and were wrong.
"""
import os
import re
import sys

NEEDLE = sys.argv[1] if len(sys.argv) > 1 else ''
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SKIP = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
        'unit_conversions', 'celebration_', 'import_recipe',
        'map_ingredients', 'measurement_units', 'household_member',
        'categories_management')

files = []
for dp, _d, ns in os.walk(ROOT):
    for n in sorted(ns):
        if not n.endswith('.html'):
            continue
        rel = os.path.relpath(os.path.join(dp, n), ROOT).replace(os.sep, '/')
        if any(s in rel for s in SKIP) or rel == 'base.html':
            continue
        if NEEDLE and NEEDLE not in rel:
            continue
        files.append((rel, os.path.join(dp, n)))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def markup(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


rows = []
for rel, p in files:
    src = read(p)
    mk = markup(src)
    css = css_of(src)

    # --- is it an entry screen? ------------------------------------------
    posts = re.findall(r'<form[^>]*method\s*=\s*["\']post["\'][^>]*>', mk,
                       re.I)
    controls = len(re.findall(r'<(?:input|select|textarea)\b', mk, re.I))
    # a hidden csrf token and a search box do not make an entry screen
    typed = len(re.findall(r'<input[^>]*type\s*=\s*["\']'
                           r'(?:hidden|submit|button|search)["\']', mk, re.I))
    real = controls - typed
    if not posts or real < 3:
        continue

    # --- the heading ------------------------------------------------------
    h2 = re.search(r'<h2([^>]*)>(.*?)</h2>', mk, re.S)
    centred = bool(h2 and '<center' in h2.group(2).lower())
    h2cls = bool(h2 and 'page-title-h2' in h2.group(1))
    h2txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '',
                                       h2.group(2) if h2 else '')).strip()
    h4 = re.search(r'<h4[^>]*page-subtitle-h4[^>]*>(.*?)</h4>', mk, re.S)
    h4txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '',
                                       h4.group(1) if h4 else '')).strip()
    # A MODE ON THE h2 is the drift the shape-B round named.
    mode_on_h2 = bool(re.match(r'^(ADD|EDIT|NEW|DELETE)\b', h2txt))

    # --- the form's anatomy ----------------------------------------------
    grid = ('form-row' if '<div class="form-row"' in mk
            else 'row' if re.search(r'<div[^>]*class="[^"]*\brow\b', mk)
            else '-')
    cols = len(re.findall(r'\bcol-md-\d+', mk))
    labels = len(re.findall(r'<label\b', mk, re.I))
    bold = len(re.findall(r'<label[^>]*>\s*<strong>', mk, re.I))
    req = len(re.findall(r'alv-req', mk))
    legacy_req = len(re.findall(r'text-danger[^"]*"\s*>\s*\*', mk))
    helptext = len(re.findall(r'form-text|text-muted small|small '
                              r'class="text-muted"', mk))
    fc = len(re.findall(r'class="[^"]*\bform-control\b', mk))

    # --- the action bar ---------------------------------------------------
    bar = ('page-action-buttons-form'
           if 'page-action-buttons-form' in mk
           else 'page-action-buttons' if 'page-action-buttons' in mk
           else 'action-bar' if 'action-bar' in mk else '-')
    save = bool(re.search(r'action-primary', mk))
    back = bool(re.search(r'action-back', mk))
    cancel = bool(re.search(r'>\s*Cancel\s*<', mk))

    # --- the local heading CSS, and the media query that fires on paper ---
    hcss = sorted(set(re.sub(r'\s+', ' ', m).strip() for m in re.findall(
        r'[^{}]*page-(?:title-h2|subtitle-h4)[^{}]*\{[^}]*\}', css)))
    naked = len(re.findall(r'@media\s*\(max-width', css))

    rows.append(dict(rel=rel, h2=h2txt, h4=h4txt, centred=centred,
                     h2cls=h2cls, mode=mode_on_h2, grid=grid, cols=cols,
                     labels=labels, bold=bold, req=req, legacy=legacy_req,
                     help=helptext, fc=fc, bar=bar, save=save, back=back,
                     cancel=cancel, hcss=hcss, naked=naked, ctrl=real))

print('\n%d ENTRY SCREEN(S) - a page that posts a form of three or more '
      'data controls\n' % len(rows) + '=' * 78)

print('\n%-38s %-5s %-5s %-4s %-4s %s'
      % ('template', 'ctrls', 'cols', 'req', 'help', 'action bar'))
print('-' * 78)
for r in rows:
    print('%-38s %5d %5d %4d %4d  %s%s%s%s'
          % (r['rel'], r['ctrl'], r['cols'], r['req'], r['help'], r['bar'],
             ' +Save' if r['save'] else '', ' +Back' if r['back'] else '',
             ' +Cancel' if r['cancel'] else ''))


def group(key, title, fmt=str):
    print('\n' + '=' * 78 + '\n' + title + '\n' + '=' * 78)
    g = {}
    for r in rows:
        g.setdefault(fmt(r[key]), []).append(r['rel'])
    for k in sorted(g, key=lambda k: (-len(g[k]), k)):
        print('\n  %-46s %2d page(s)' % (k[:46], len(g[k])))
        for x in g[k]:
            print('      %s' % x)


group('centred', 'HEADING ALIGNMENT - centred, or left where the standard '
      'says centred', lambda v: 'centred' if v else 'LEFT-ALIGNED (or no h2)')
group('h2cls', 'DOES THE TITLE CARRY page-title-h2?',
      lambda v: 'yes' if v else 'no')
group('mode', 'IS A MODE LABEL SITTING ON THE h2, WHERE THE MODULE NAME '
      'BELONGS?', lambda v: 'YES - drift' if v else 'no')
group('grid', 'THE FORM GRID')
group('bar', 'THE ACTION BAR CLASS')

print('\n' + '=' * 78)
print('REQUIRED MARKERS - .alv-req is the standard; text-danger is the old '
      'one')
print('=' * 78)
for r in rows:
    if r['legacy']:
        print('  %-38s %2d alv-req, %2d LEGACY text-danger'
              % (r['rel'], r['req'], r['legacy']))
_none = [r['rel'] for r in rows if not r['req'] and not r['legacy']]
print('\n  %d screen(s) mark nothing as required at all:' % len(_none))
for x in _none:
    print('      %s' % x)

print('\n' + '=' * 78)
print('THE HEADING CSS, PER PAGE - base declares neither class')
print('=' * 78)
seen = {}
for r in rows:
    for rule in r['hcss']:
        seen.setdefault(rule, []).append(r['rel'])
print('  %d distinct local rule(s) among the entry screens alone' % len(seen))
for k in sorted(seen, key=lambda k: -len(seen[k])):
    print('    %-62s %d' % (k[:62], len(seen[k])))
_paper = [r['rel'] for r in rows if r['naked']]
print('\n  %d screen(s) write `@media (max-width: ...)` with no `screen`, so '
      'the rule\n  fires on paper (A4 portrait is about 718 CSS px):'
      % len(_paper))
for x in _paper:
    print('      %s' % x)
