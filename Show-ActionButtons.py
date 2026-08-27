"""Show-ActionButtons - who has page-header action buttons, and what colour.

    python Show-ActionButtons.py
    python Show-ActionButtons.py --full properties.html

READ ONLY. Writes nothing, changes nothing.

WHY
---
base.html already owns the ROW-level action vocabulary - .icon-action-btn
plus .icon-edit / .icon-view / .icon-delete, with their colours coming from
--alv-edit / --alv-view / --alv-danger.

It owns NOTHING of the PAGE-header bar. Not one .action-* rule is in
base.html - measured, after I first mis-read a mention inside a comment as a
definition. .page-action-buttons, .action-primary, .action-secondary,
.action-add-new, .action-back and the mobile More menu are defined per page,
or not at all, and the colour comes from whichever Bootstrap class the page
reached for that day.

That is the same shape as the tables before this project started: a real
shared component with no single home. This script measures how big it is
before anyone commits to a design.

WHAT IT REPORTS
---------------
1. Where the page-header bar is defined, and how many rules each page spends
   on it.
2. The colour census - which Bootstrap button class each page uses in its
   header bar, so "yellow means edit" can be checked rather than assumed.
3. Every distinct button LABEL, so the verbs can be seen at once.
4. What a conversion would have to touch.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

if not os.path.isdir(TPL):
    sys.exit('! pages/templates not found - run from the project root')

FULL = None
if '--full' in sys.argv:
    i = sys.argv.index('--full')
    if i + 1 < len(sys.argv):
        FULL = sys.argv[i + 1]

# The classes that make up the page-header bar. base.html defines none of
# them today - section 1 prints what it does define, so the claim is checked
# rather than asserted.
BAR = ('.page-action-buttons', '.action-primary', '.action-secondary',
       '.action-add-new', '.action-back', '.action-more-btn',
       '.action-more-menu', '.action-more-item')

BOOTSTRAP_BTN = ('btn-info', 'btn-primary', 'btn-secondary', 'btn-success',
                 'btn-warning', 'btn-danger', 'btn-light', 'btn-dark',
                 'btn-outline-info', 'btn-outline-secondary',
                 'btn-outline-danger')


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


def strip_css_comments(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def css_of(t):
    return strip_css_comments(
        ''.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)))


def markup_of(t):
    t = re.sub(r'<style[^>]*>.*?</style>', ' ', t, flags=re.S | re.I)
    return re.sub(r'<script[^>]*>.*?</script>', ' ', t, flags=re.S | re.I)


def rule_starts(css, name):
    """The BRACE POSITIONS of rules whose selector names this class.

    Positions, not a count, because a selector like
    `.page-action-buttons .action-back` names two of them and would be
    counted twice - which is how the first draft of this script turned
    9 real rules in asset_detail.html into "17 rules". Callers union the
    sets, so each rule is counted once however many names it carries.

    Boundary-aware too: a plain \\b matches across a hyphen, so
    `\\b.action-back\\b` also matched `.action-back-label`. That produced a
    false alarm on this project once already.
    """
    return set(m.end() for m in re.finditer(
        r'(?<![\w-])%s(?![\w-])[^{}]*\{' % re.escape(name), css))


def rules_naming(css, names):
    """How many DISTINCT rules name any of these classes."""
    if isinstance(names, str):
        names = (names,)
    out = set()
    for n in names:
        out |= rule_starts(css, n)
    return len(out)


files = sorted(f for f in os.listdir(TPL)
               if f.endswith('.html') and '.bak' not in f)

if FULL:
    p = os.path.join(TPL, FULL)
    if not os.path.exists(p):
        sys.exit('! %s not found' % FULL)
    t = read(p)
    m = markup_of(t)
    print('')
    print('=' * 74)
    print(' %s - every page-header action, verbatim' % FULL)
    print('=' * 74)
    hit = False
    for mm in re.finditer(r'<(a|button|span)\b[^>]*class="[^"]*'
                          r'(?:action-(?:primary|secondary|add-new|back|'
                          r'more-btn|more-item)|btn-(?:info|warning|danger|'
                          r'success|primary))[^"]*"[^>]*>(.*?)</\1>',
                          m, re.S):
        hit = True
        tag = mm.group(0)
        label = ' '.join(re.sub(r'<[^>]+>', ' ', mm.group(2)).split())
        cls = re.search(r'class="([^"]*)"', tag)
        print('')
        print('  <%s class="%s">' % (mm.group(1), cls.group(1) if cls else ''))
        print('     label: %s' % (label or '(icon only)'))
    if not hit:
        print('')
        print('  nothing matched - this page has no page-header action bar.')
    print('')
    sys.exit(0)

rows = []
for f in files:
    t = read(f if os.path.isabs(f) else os.path.join(TPL, f))
    c, m = css_of(t), markup_of(t)
    if '.page-action-buttons' not in c and 'page-action-buttons' not in m:
        continue
    local = rules_naming(c, BAR)
    colours = dict((b, len(re.findall(r'(?<![\w-])%s(?![\w-])' % b, m)))
                   for b in BOOTSTRAP_BTN)
    labels = []
    for mm in re.finditer(r'<(a|button|span)\b[^>]*class="[^"]*'
                          r'action-(?:primary|secondary|add-new|back)'
                          r'[^"]*"[^>]*>(.*?)</\1>', m, re.S):
        lab = ' '.join(re.sub(r'<[^>]+>', ' ', mm.group(2)).split())
        lab = re.sub(r'\{[{%][^}%]*[%}]\}', '', lab).strip()
        if lab:
            labels.append(lab)
    rows.append((f, local, local, colours, labels,
                 c.count('\n') + 1))

if not rows:
    print('')
    print('  No template carries a .page-action-buttons bar. Nothing to do.')
    sys.exit(0)

print('')
print('=' * 74)
print(' 1. WHO HAS A PAGE-HEADER ACTION BAR, AND WHO PAYS FOR IT')
print('=' * 74)
print('')
print('  base.html defines: %s'
      % (', '.join(b for b in BAR
                   if rules_naming(css_of(read(os.path.join(TPL, 'base.html'))),
                                   b)) or '(none)'))
print('')
print('  %-38s %5s  %5s' % ('template', 'rules', 'css lines'))
print('  ' + '-' * 52)
total = 0
for f, n, _, _, _, lines in sorted(rows, key=lambda r: -r[1]):
    total += n
    print('  %-38s %5d  %5d' % (f[:38], n, lines))
print('  ' + '-' * 52)
print('  %-38s %5d      across %d template(s)' % ('TOTAL', total, len(rows)))
print('')
print('  Every one of those rules is a copy of the same component.')

print('')
print('=' * 74)
print(' 2. THE COLOUR CENSUS - does a colour mean anything today?')
print('=' * 74)
print('')
tally = {}
for _, _, _, colours, _, _ in rows:
    for k, v in colours.items():
        tally[k] = tally.get(k, 0) + v
print('  %-24s %6s   %s' % ('bootstrap class', 'uses', 'files'))
print('  ' + '-' * 56)
for k in BOOTSTRAP_BTN:
    n = tally.get(k, 0)
    if not n:
        continue
    where = [f for f, _, _, colours, _, _ in rows if colours.get(k)]
    print('  %-24s %6d   %s' % (k, n, ', '.join(w[:-5] for w in where[:4])
                                + (' +%d' % (len(where) - 4)
                                   if len(where) > 4 else '')))
print('')

print('=' * 74)
print(' 3. THE VERBS - what these buttons actually say')
print('=' * 74)
print('')
verbs = {}
for f, _, _, _, labels, _ in rows:
    for lab in labels:
        verbs.setdefault(lab, []).append(f)
for lab in sorted(verbs, key=lambda x: -len(verbs[x])):
    print('  %-28s x%-3d  %s'
          % (lab[:28], len(verbs[lab]),
             ', '.join(w[:-5] for w in verbs[lab][:3])
             + (' +%d' % (len(verbs[lab]) - 3) if len(verbs[lab]) > 3 else '')))
print('')

print('=' * 74)
print(' 4. WHAT A CONVERSION WOULD TOUCH')
print('=' * 74)
print('')
print('  templates with a bar ................ %d' % len(rows))
print('  local rules that would be deleted ... %d' % total)
mixed = [f for f, _, _, colours, _, _ in rows
         if sum(1 for k in ('btn-warning', 'btn-danger', 'btn-success',
                            'btn-primary') if colours.get(k)) >= 2]
print('  pages using 2+ colours in the bar ... %d  (%s)'
      % (len(mixed), ', '.join(m[:-5] for m in mixed[:6])
         + (' +%d' % (len(mixed) - 6) if len(mixed) > 6 else '')))
print('')
print('  Run  python Show-ActionButtons.py --full <file>  to see one page.')
print('')
