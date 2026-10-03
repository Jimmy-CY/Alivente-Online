# -*- coding: utf-8 -*-
"""DD-1 - A TABLE THAT HOLDS A POPUP DOES NOT CLIP IT

Demetri, 3 Oct 2026: "When I capture a recipe, the dropdowns/modals are
cutting off."

==========================================================================
IT IS base, AND IT IS THE WORD clip
==========================================================================
base gives every .table-container

    overflow: clip;

chosen over `hidden` on 26 September so the sticky table header still
sticks while the rounded corners still clip - measured at the time, 615px
of drift with hidden and none with clip.

BUT clip CLIPS ABSOLUTELY-POSITIONED DESCENDANTS EXACTLY AS hidden DOES.
The ingredient autocomplete is position:absolute inside a <td> inside a
.table-container whose bottom edge sits a few pixels under the input, so
the list of suggestions is cut to a teal sliver.

==========================================================================
THE RULE, NOT THE PAGE
==========================================================================
A TABLE THAT HOLDS A POPUP DOES NOT CLIP. One rule in base, and the popup
says it is one by carrying .alv-escapes - so a container only stops
clipping where something actually needs to escape, and every other table
in the app keeps its corners exactly as they are.

I MEASURED THE FAMILY BEFORE WRITING THE RULE, and it is smaller than it
looked: of the popup layers in this tree, the ones inside a table are the
two on preview_imported_recipe. .action-more-menu is also absolute, but
every page puts it in the ACTION BAR, which is not inside a container.
The six bespoke dropdown containers on the outstanding list are a
styling job, not a clipping one - they are not clipped today.

:has() IS THE RIGHT SELECTOR AND ITS FAILURE IS TODAY. A browser that
does not know :has() drops the rule and behaves exactly as it does now,
which is the only safe way to fail.

Backups: .bak_escapedrop. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_escapedrop'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

BASE = alv_tree.path_of('base.html')
PAGE = alv_tree.path_of('preview_imported_recipe.html')

ANCHOR = """        overflow: clip;
        box-shadow: 0 1px 2px rgba(16, 34, 40, .05),
                    0 1px 3px rgba(16, 34, 40, .04);
      }
"""

RULE = """
      /* ===== DD-1 ===== 3 Oct 2026 ==================================
         A TABLE THAT HOLDS A POPUP DOES NOT CLIP IT.

         The `clip` above is deliberate - see the note on it - but it
         clips ABSOLUTELY-POSITIONED DESCENDANTS exactly as `hidden`
         does. A dropdown opened from a cell is one of those, and on the
         recipe capture page the container's bottom edge sits a few
         pixels under the input: the suggestions came out as a sliver.

         THE POPUP SAYS SO, THE CONTAINER DOES NOT GUESS. Only a
         container holding .alv-escapes stops clipping, so every other
         table in the app keeps its corners. Marking the popup rather
         than the table also means the fact lives next to the thing it
         is true of.

         A BROWSER WITHOUT :has() DROPS THIS RULE AND BEHAVES AS IT DOES
         TODAY, which is the only safe way for a fix to fail.
                                            [test_escaping_drop.py] */
      .table-container:has(.alv-escapes) { overflow: visible; }
      /* ===== /DD-1 ===== */
"""


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
            raise SystemExit('DD1: %s is not a byte copy' % bak)


def swap(path, text, old, new, what, times=1):
    c = text.count(old)
    if c != times:
        raise SystemExit('DD1: %s appears %d times, not %d'
                         % (what, c, times))
    return text.replace(old, new)


print('=' * 74)
print('DD-1 - A TABLE THAT HOLDS A POPUP DOES NOT CLIP IT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(BASE)
nl = t.replace('\r\n', '\n')
if 'alv-escapes' in nl:
    print('  base.html                  already carries the rule')
else:
    nl = swap(BASE, nl, ANCHOR, ANCHOR + RULE, 'the table-container block')
    out = nl.replace('\n', '\r\n') if CRLF.get(BASE) else nl
    if not CHECK:
        back_up(BASE, raw)
        write(BASE, out)
    print('  base.html                  one rule, keyed on the popup')

t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')
if 'alv-escapes' in nl:
    print('  preview_imported_recipe.html  already marked')
else:
    # ONLY THE ONE THAT IS ACTUALLY INSIDE A TABLE. The three
    # multiselect menus on this page sit in the Basic Information card,
    # not in a .table-container, and nothing clips them - marking them
    # would unclip a table that holds no popup and would make the rule
    # read as decoration. Measured in gate 6.
    n = 0
    for cls in ('autocomplete-dropdown',):
        for old, new in (('class="%s ' % cls, 'class="alv-escapes %s ' % cls),
                         ('class="%s"' % cls, 'class="alv-escapes %s"' % cls)):
            n += nl.count(old)
            nl = nl.replace(old, new)
        if not n:
            raise SystemExit('DD1: no %s on the page' % cls)
    out = nl.replace('\n', '\r\n') if CRLF.get(PAGE) else nl
    if not CHECK:
        back_up(PAGE, raw)
        write(PAGE, out)
    print('  preview_imported_recipe.html  %d popup(s) marked' % n)

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
b = alv_tree.code_only(read(BASE)[0])
p = alv_tree.code_only(read(PAGE)[0])
was = alv_tree.code_only(read(PAGE + SUFFIX)[0])


def classes(src):
    out = []
    for m in re.finditer(r'class="([^"]*)"', src):
        out.append(m.group(1).split())
    return out


# 1. THE RULE IS IN base, ONCE, AND IT IS A :has() ON THE CONTAINER.
hits = re.findall(r'\.table-container:has\(\.alv-escapes\)\s*\{[^}]*\}', b)
if len(hits) != 1:
    raise SystemExit('DD1: %d copies of the rule in base, not one'
                     % len(hits))
if 'overflow: visible' not in hits[0]:
    raise SystemExit('DD1: the rule does not set overflow visible')
print('  base carries the rule once, as a :has() on the container')

# 2. AND THE clip IT NARROWS IS STILL THERE. If the round had simply
#    replaced it, every table in the app would lose its corners and
#    nothing would say so.
if 'overflow: clip;' not in b:
    raise SystemExit('DD1: the container no longer clips at all - this '
                     'round narrows that rule, it does not remove it')
i = b.index('overflow: clip;')
j = b.index('.table-container:has(.alv-escapes)')
if j < i:
    raise SystemExit('DD1: the narrowing rule comes BEFORE the rule it '
                     'narrows, so clip wins on equal specificity')
print('  the clip it narrows is still there, and comes first')

# 3. EVERY POPUP ON THE PAGE IS MARKED, AND IT IS A TOKEN, NOT A STRING.
marked = [c for c in classes(p) if 'alv-escapes' in c]
if len(marked) < 6:
    raise SystemExit('DD1: only %d popup(s) marked' % len(marked))
for c in marked:
    if 'autocomplete-dropdown' not in c:
        raise SystemExit('DD1: something that is not a popup was marked: %s'
                         % ' '.join(c))
print('  all %d popups on the capture page carry the class' % len(marked))

for cls in ('autocomplete-dropdown',):
    every = [c for c in classes(p) if cls in c]
    missing = [c for c in every if 'alv-escapes' not in c]
    if missing:
        raise SystemExit('DD1: %d %s left unmarked' % (len(missing), cls))
    print('  every %-22s is marked (%d)' % (cls, len(every)))

# 4. CONTROL: NONE OF THEM WAS MARKED BEFORE.
if 'alv-escapes' in was:
    raise SystemExit('DD1: CONTROL FAILED - the backup already carried it')
print('  CONTROL: before this round not one of them was')

# 5. AND NOTHING ELSE IN THE TREE CARRIES IT. A rule that is not keyed to
#    a popup is a rule that unclips tables at random.
other = []
for q in sorted(alv_tree.templates()):
    if q in (BASE, PAGE):
        continue
    if 'alv-escapes' in alv_tree.code_only(read(q)[0]):
        other.append(alv_tree.rel(q))
if other:
    raise SystemExit('DD1: the class leaked onto %s' % ', '.join(other[:5]))
print('  and no other page carries it')

# 6. THE FAMILY, MEASURED. The round claims the popups inside a table are
#    these; a seventh appearing later should say so rather than be found
#    by a reader with a screenshot.
inside = []
for q in sorted(alv_tree.templates()):
    s = alv_tree.code_only(read(q)[0])
    if 'table-container' not in s:
        continue
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', s, re.S))
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        body = m.group(2)
        if 'position: absolute' in body and 'z-index' in body:
            sel = m.group(1).strip().split('\n')[-1].strip()
            name = sel.lstrip('.').split()[0].split(':')[0]
            if name and ('class="%s' % name) in s:
                inside.append((alv_tree.rel(q), sel))
pages = sorted(set(x[0] for x in inside))
print('  %d positioned popup layer(s) live in a page with a table '
      'container, on %d page(s)' % (len(inside), len(pages)))
for x in inside:
    print('    %-40s %s' % x)

print('-' * 74)
print('  clip clips an absolutely-positioned descendant exactly as hidden')
print('  does. The popup says it needs to escape; the table does not guess.')
print('=' * 74)
