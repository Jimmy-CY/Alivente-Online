# -*- coding: utf-8 -*-
"""SECTION I, ROUND I1 - TEN PAGES STOP STRETCHING THEIR ACTION BAR

Demetri, on Issues (Comments) at 386px: "This is not right in Issues."

MEASURED, on fsr_details, at his width:

    Edit Issue    34px wide, and its text overflowing the box
    Back         386px wide, starting at x=42, running off the screen

That is the screenshot. The cause is one rule the page keeps for itself:

    @media (max-width: 768px) {
        .page-action-buttons > .btn,
        .page-action-buttons > a { width: 100%; text-align: center; }
    }

base's phone rules for that bar are already right, and have been since
the action-bar round:

    .page-action-buttons { flex-direction: row; nowrap; gap: 8px; }
    .page-action-buttons .action-primary { flex: 1 1 auto; min-width: 0; }
    .page-action-buttons .action-back    { width: 44px; height: 44px; }

`.page-action-buttons .btn` and `.page-action-buttons .action-back` have
the SAME specificity, so the later stylesheet wins - and a page's style
block comes after base's. The page wins, both controls demand the whole
width of a phone in a nowrap row, they squash each other, and min-width:0
lets the primary shrink below its own text. Hence 34px of button holding
the words Edit Issue.

WITH THE RULE GONE: Edit Issue 334px, Back a 44px square at x=342.
334 + 8 + 44 = 386. Nothing is added to base; base was always going to do
this.

THIS IS THE THIRD TIME. T1 removed it from the report heads, where it
was base's own rule and Back came out 362px wide. D1 removed
`.page-header-actions .btn { width: 100% }` from property_detail the
moment that page was given a Back. This round finds the rest of them by
asking the question those two answered one page at a time - which pages
set a width on a button inside an action bar - and there are TEN.

    customer_form                 finance_valuations_add
    finance_valuations_edit       fsr_details
    projects/project_subtasks_add projects/project_tasks_add
    projects/project_tasks_delete projects/project_tasks_edit
    projects/projects_add         projects/projects_edit

EVERY ONE OF THE TEN HAS A BACK, so every one of them is wrong in the
same way. project_tasks_delete has NOTHING BUT a Back, stretched across
the phone - which is character for character the defect T1 existed to
remove.

WHAT ELSE THE RULES SAID. Six of the ten also set padding: 14px,
font-size: 15px and margin: 0 !important on the same selector. Those go
with it: base sets the height, the padding and the gap for this bar, and
a page setting its own was the same mistake in a different declaration.
Every one of the ten is drawn before and after.

Backups: .bak_barstretch. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_barstretch'
CRLF = {}

PAGES = ('customer_form.html', 'finance_valuations_add.html',
         'finance_valuations_edit.html', 'fsr_details.html',
         os.path.join('projects', 'project_subtasks_add.html'),
         os.path.join('projects', 'project_tasks_add.html'),
         os.path.join('projects', 'project_tasks_delete.html'),
         os.path.join('projects', 'project_tasks_edit.html'),
         os.path.join('projects', 'projects_add.html'),
         os.path.join('projects', 'projects_edit.html'))

# A rule that sets a width on a BUTTON inside the bar. The container's
# own width is a different thing and is left alone - properties_edit and
# tenant_edit size .page-action-buttons-edit, which is the wrapper.
# IT MUST SET A WIDTH. The first version matched any rule on a button in
# the bar and found two on fsr_details - the second being a harmless
# `.page-action-buttons > .btn { margin-right: 0; }` at the top level,
# which is not this defect and is not this round's business.
DEAD = re.compile(r'(?m)^[ \t]*\.page-action-buttons\s*>?\s*'
                  r'(?:\.btn|a|button)\b[^{}]*\{[^}]*\bwidth\s*:'
                  r'[^{}]*\}\n?')

NOTE = """        /* The rule that was here set width: 100% on every button in
           this bar below 768px. base already sizes them - the primary
           grows, Back is a 44px square - and the two selectors have the
           same specificity, so this one won on stylesheet order alone.
           Demetri saw the result on Issues: a 34px Edit Issue with its
           text overflowing, beside a 386px Back running off the screen.
           30 Sep 2026.                    [test_bar_stretch.py] */
"""


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('I1: %s is not a byte copy' % bak)


# TWO MORE, FOUND BY THE GATE RATHER THAN BY THE SCREENSHOT.
# finance_expense_types and finance_revenue_types carry a near-complete
# COPY of base's phone bar - the primary, the secondary and Back - with
# 38px where base says 44px.
#
# MEASURED BEFORE DECIDING: the heights are already 44px, because a later
# rule of base's wins, so the 38px never applied at all. The one live
# effect of twenty lines of copied CSS is BACK AT 50px instead of 44px.
# That is the whole change on these two, and it is still worth making:
# every other Back in the system is a 44px square.
COPIES = ('finance_expense_types.html', 'finance_revenue_types.html')
COPY = re.compile(r'(?m)^[ \t]*\.page-action-buttons \.(?:action-primary|'
                  r'action-back|action-secondary)\b[^{}]*\{[^}]*\}\n?')
COPY_NOTE = """        /* Three rules were here - .action-primary, .action-secondary
           and .action-back - copying base's phone bar with 38px where
           base says 44px. The heights never applied; a later rule of
           base's won. The one thing that did was Back at 50px, where
           every other Back in the system is a 44px square.
           30 Sep 2026.                    [test_bar_stretch.py] */
"""

# ==========================================================================
print('=' * 74)
print('SECTION I, ROUND I1 - TWELVE PAGES STOP SIZING THEIR ACTION BAR%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

done = 0
for rel in PAGES:
    p = alv_tree.join(rel)
    if not os.path.isfile(p):
        raise SystemExit('I1: %s is not where alv_tree says' % rel)
    t, raw = read(p)
    shown = rel.replace(os.sep, '/')
    if 'test_bar_stretch.py' in t:
        print('  %-38s already done' % shown)
        continue

    a = t.find('<style')
    b = t.find('</style>', a)
    if a < 0 or b < 0:
        raise SystemExit('I1: %s has no style block' % shown)
    css = t[a:b]
    hits = DEAD.findall(css)
    if len(hits) != 1:
        raise SystemExit('I1: %s - %d rule(s) to remove, not 1: %s'
                         % (shown, len(hits),
                            [' '.join(h.split())[:60] for h in hits]))
    # IT MUST BE A PHONE RULE. One of these at the top level would be
    # changing the desktop too, and this round is about the phone.
    at = DEAD.search(css).start()
    depth = css.count('{', 0, at) - css.count('}', 0, at)
    if depth != 1:
        raise SystemExit('I1: %s - the rule is at depth %d, not inside a '
                         'media block' % (shown, depth))
    said = ' '.join(hits[0].split())
    css2 = css[:at] + eol(p, NOTE) + DEAD.sub('', css[at:])
    t = t[:a] + css2 + t[b:]
    print('  %-38s %s' % (shown, said[:76]))

    # GATES.
    css3 = re.sub(r'/\*.*?\*/', ' ', t[a:t.find('</style>', a)], flags=re.S)
    if DEAD.search(css3):
        raise SystemExit('I1: %s still sets a width on a bar button' % shown)
    for m in re.finditer(r'([^{}]*page-action-buttons[^{}]*)\{([^}]*)\}',
                         css3):
        sel = ' '.join(m.group(1).split())
        if re.search(r'\b(?:btn|action-|a|button)\b', sel) \
                and re.search(r'\bwidth\s*:', m.group(2)):
            raise SystemExit('I1: %s still sizes a button in the bar: %s'
                             % (shown, sel[:70]))
    # THE MARKUP IS NOT TOUCHED. This round is CSS.
    strip = lambda s: re.sub(r'<style\b.*?</style>', '', s, flags=re.S)
    if strip(raw.decode('utf-8')) != strip(t):
        raise SystemExit('I1: %s - the markup changed, and it should not '
                         'have' % shown)
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    done += 1

for rel in COPIES:
    p = alv_tree.join(rel)
    t2, raw2 = read(p)
    if 'test_bar_stretch.py' in t2:
        print('  %-38s already done' % rel)
        continue
    a = t2.find('<style')
    b = t2.find('</style>', a)
    css = t2[a:b]
    hits = COPY.findall(css)
    if len(hits) != 3:
        raise SystemExit('I1: %s - %d copied rule(s), not 3' % (rel, len(hits)))
    at = COPY.search(css).start()
    depth = css.count('{', 0, at) - css.count('}', 0, at)
    if depth != 1:
        raise SystemExit('I1: %s - the copy is at depth %d, not in a media '
                         'block' % (rel, depth))
    css2 = css[:at] + eol(p, COPY_NOTE) + COPY.sub('', css[at:])
    t2 = t2[:a] + css2 + t2[b:]
    print('  %-38s three copied rules out; Back goes 50px -> 44px' % rel)
    left = re.sub(r'/\*.*?\*/', ' ', t2[a:t2.find('</style>', a)], flags=re.S)
    if COPY.search(left):
        raise SystemExit('I1: %s still copies base\'s bar' % rel)
    strip = lambda s: re.sub(r'<style\b.*?</style>', '', s, flags=re.S)
    if strip(raw2.decode('utf-8')) != strip(t2):
        raise SystemExit('I1: %s - the markup changed' % rel)
    if not CHECK:
        back_up(p, raw2)
        write(p, t2)
    done += 1

print('-' * 74)
print('  %d page(s) changed; base sizes these bars now, as it always could'
      % done)

# ---- what is NOT in this round ------------------------------------------
print('  reported, not changed')
for rel, why in (('properties_edit.html', 'sizes .page-action-buttons-edit, '
                  'which is the WRAPPER, not a button'),
                 ('tenant_edit.html', 'the same wrapper rule'),
                 ('recipe_management.html', 'sizes a dropdown inside the '
                  'bar, which base has no name for')):
    q = alv_tree.path_of(rel)
    if not os.path.isfile(q):
        raise SystemExit('I1: %s is not where alv_tree says' % rel)
    print('     %-30s %s' % (rel, why))

twice = []
for rel in PAGES:
    q = alv_tree.join(rel)
    body = re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', read(q)[0], flags=re.S), flags=re.S)
    m = re.search(r'<div[^>]*class="[^"]*page-action-buttons[^"]*"[^>]*>',
                  body)
    if not m:
        continue
    i, d = m.start(), 0
    for x in re.finditer(r'<div\b|</div>', body[i:]):
        d += 1 if x.group(0) != '</div>' else -1
        if d == 0:
            seg = body[i:i + x.end()]
            break
    # AS A TOKEN. \baction-back\b also matches inside
    # action-back-label, which reported nine of the ten as carrying two
    # Backs when two of them do.
    if len(re.findall(r'action-back(?![\w-])', seg)) > 1:
        twice.append(rel.replace(os.sep, '/'))
if twice:
    print('     %-30s carry TWO action-back buttons in one bar - not this'
          % '')
    for r in twice:
        print('        %s' % r)
    print('        round\'s business, but nobody meant to draw Back twice.')

print('-' * 74)
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
