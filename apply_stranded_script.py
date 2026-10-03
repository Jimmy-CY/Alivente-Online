# -*- coding: utf-8 -*-
"""IB-2 - SEVENTY LINES OF SCRIPT THAT DJANGO THREW AWAY

Demetri, 3 Oct 2026, of Ingredient Shopping Units: "Search by name field
works perfectly. The Category dropdown does nothing even when a category
is selected."

==========================================================================
IT IS NOT THE DROPDOWN
==========================================================================
The select has a change handler, written by IB-1 on 2 October:

    categorySelect.addEventListener('change', function () { form.submit(); });

and the view reads request.GET['category'] and filters on it. Both halves
are correct. They never meet, because the script holding that handler is
written AFTER the page's {% endblock %}.

A CHILD TEMPLATE IS NOT A DOCUMENT. It is a set of blocks, and anything
outside a block is DISCARDED - no warning, no error, no output. Those
2,598 characters have never reached a browser.

==========================================================================
SO FOUR THINGS WERE BROKEN, NOT ONE
==========================================================================
Everything in that script went with it:

    the Category filter        change -> submit
    the chip row               so the Filter badge has read 0 since IB-1
    Clear All                  it clears nothing
    Enter in the search box    it does not reach the server

Search still narrowed because THAT half lives in base - data-live-search
- and base renders.

==========================================================================
AND IT IS THE ONLY ONE
==========================================================================
Measured across every template that extends another: one page strands
anything after its last endblock, and this is it. The gate is kept, so a
second one cannot appear quietly.

Backups: .bak_stranded. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_stranded'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

PAGE = alv_tree.path_of('ingredient_base_units_management.html')
END = '{% endblock %}'


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
            raise SystemExit('IB2: %s is not a byte copy' % bak)


def stranded(src):
    """What a child template puts outside every block, and therefore
    throws away. Returns (start, end) of the run after the LAST endblock,
    or None.

    Read off the markup with comments blanked: a template that merely
    DISCUSSES an endblock in a comment has not closed a block. That is
    the lesson this tree has learned five times now, and it would bite
    here harder than most - the string this looks for is one a note about
    this very round would want to quote."""
    code = alv_tree.code_only(src).replace('\r\n', '\n')
    if not re.search(r'\{%\s*extends\b', code):
        return None
    last = None
    for m in re.finditer(r'\{%\s*endblock[^%]*%\}', code):
        last = m
    if last is None:
        return None
    tail = code[last.end():]
    return (last.end(), len(code)) if tail.strip() else None


print('=' * 74)
print('IB-2 - THE SCRIPT DJANGO THREW AWAY%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')
span = stranded(nl)

if span is None:
    print('  ingredient_base_units_management.html   nothing stranded')
else:
    body = nl[span[0]:span[1]]
    print('  %d characters are outside every block and never render'
          % len(body.strip()))
    # It is MOVED, not rewritten. The handlers IB-1 wrote are right; the
    # only thing wrong with them is where they sit.
    i = nl.rindex(END)
    moved = (nl[:i].rstrip('\n')
             + '\n\n'
             + '{# IB-2, 3 Oct 2026 - THIS SCRIPT USED TO SIT BELOW THE  #}\n'
             + '{# endblock, where Django discards it without a word. It #}\n'
             + '{# took the Category filter, the chip row, Clear All and #}\n'
             + '{# Enter-to-search down with it. Moved, not rewritten -  #}\n'
             + '{# the handlers were always right.   [test_stranded.py]  #}\n'
             + body.strip()
             + '\n\n' + END + '\n')
    if CRLF.get(PAGE):
        moved = moved.replace('\n', '\r\n')
    if not CHECK:
        back_up(PAGE, raw)
        write(PAGE, moved)
    print('  moved inside the content block, unchanged')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
now = read(PAGE)[0].replace('\r\n', '\n')
was = read(PAGE + SUFFIX)[0].replace('\r\n', '\n')
code = alv_tree.code_only(now)

# 1. NOTHING IS OUTSIDE A BLOCK ANY MORE - here, or anywhere.
left = []
for p in sorted(alv_tree.templates()):
    s = read(p)[0]
    if stranded(s.replace('\r\n', '\n')):
        left.append(alv_tree.rel(p))
if left:
    raise SystemExit('IB2: %d template(s) still strand markup: %s'
                     % (len(left), ', '.join(left[:6])))
print('  no template in the tree puts markup outside every block')

# 2. CONTROL: THE BACKUP DID. A gate that cannot fail proves nothing, and
#    this one measures the round against the file it changed.
if not stranded(was):
    raise SystemExit('IB2: CONTROL FAILED - the backup strands nothing, so '
                     'gate 1 would pass whatever this round did')
a, b = stranded(was)
print('  CONTROL: before this round, %d characters sat outside every block'
      % len(was[a:b].strip()))

# 3. THE FOUR THINGS THAT WENT WITH IT ARE BACK, AND INSIDE THE BLOCK.
i = code.rindex(END)
inside = code[:i]
for probe, what in (
        ("categorySelect.addEventListener('change'", 'the Category filter'),
        ('function updateActiveFilters', 'the chip row'),
        ("clearAllBtn.addEventListener('click'", 'Clear All'),
        ("searchInput.addEventListener('keypress'", 'Enter to search')):
    if probe not in inside:
        raise SystemExit('IB2: %s is not inside the block' % what)
    print('  %-22s is inside the block and will render' % what)

# 4. MOVED, NOT REWRITTEN. Byte for byte, with only whitespace allowed to
#    differ - otherwise this round is quietly a rewrite of IB-1's logic.
def squash(x):
    return re.sub(r'\s+', ' ', x).strip()


old_tail = squash(was[a:b])
if old_tail not in squash(now):
    raise SystemExit('IB2: the moved script is not the script that moved')
print('  and it is the same script, character for character')

# 5. THE PAGE STILL HAS ITS ONE CONTENT BLOCK, OPENED AND CLOSED ONCE.
opens = len(re.findall(r'\{%\s*block\s+content\s*%\}', code))
closes = len(re.findall(r'\{%\s*endblock[^%]*%\}', code))
if opens != 1:
    raise SystemExit('IB2: %d content block(s), not one' % opens)
if closes != len(re.findall(r'\{%\s*block\b', code)):
    raise SystemExit('IB2: %d block(s) opened, %d closed'
                     % (len(re.findall(r'\{%\s*block\b', code)), closes))
print('  %d block(s) opened and %d closed' % (
    len(re.findall(r'\{%\s*block\b', code)), closes))

# 6. AND THE VIEW READS WHAT THE SELECT POSTS. The handler submits a form
#    whose select is name="category"; a view that read something else
#    would leave the dropdown just as dead.
v = read(os.path.join(ROOT, 'pages', 'views', 'recipes',
                      'conversions.py'))[0]
if "request.GET.get('category'" not in v:
    raise SystemExit('IB2: the view does not read GET category - the '
                     'handler would submit into nothing')
if 'name="category"' not in code:
    raise SystemExit('IB2: the select is not named category')
print('  the select posts name=category and the view reads it')

print('-' * 74)
print('  A child template is not a document. Anything outside a block is')
print('  discarded with no warning, and seventy lines went that way on')
print('  2 October - the Category filter, the chips, Clear All and Enter.')
print('=' * 74)
