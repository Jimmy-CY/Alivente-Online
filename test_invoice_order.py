# -*- coding: utf-8 -*-
"""test_invoice_order.py - Section RA round RA-4, 5 Oct 2026.

RA-3b wrapped the form-shaped buttons, and the drift report - able to
read those groups for the first time - said physical_invoice_list.html
was out of order. This put it right.

IT WAS REAL, NOT AN ARTEFACT, and section 2 is the proof. Those six
controls sit in mutually exclusive {% if %} branches and the report
reads SOURCE order, so the question was which can appear TOGETHER on one
row. A draft customer invoice shows approve, duplicate, delete and pdf; an
approved one shows unapprove, send, duplicate and pdf. Four at once, both
times, and in both the PDF was last and Delete came before it.

SECTION 4 IS HERE BECAUSE THE ROUND GOT IT WRONG FIRST. The reorder
passed every gate it had - same length, same blocks, same sorted
contents, a clean permutation. But RA-3b had put the .row-actions opening
tag immediately inside that cell, so the text before the first {% if %}
IS that tag. Letting it ride with the block that followed moved the
wrapper with it, and the PDF and duplicate ended up outside the group.
A length check cannot see a tag that merely moved. So this suite reads
the wrapper back and counts what is inside it.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree
import alv_rowactions as RA

try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_invorder'
ME = 'test_invoice_order.py'
PATCHER = 'apply_invoice_order.py'
PS1 = 'Push-PendingChanges.ps1'

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


def path_of(rel):
    hits = [q for q in alv_tree.templates()
            if alv_tree.rel(q).replace(os.sep, '/') == rel]
    return hits[0] if hits else None


print(__doc__.strip().splitlines()[0])


from apply_invoice_order import WANT, CELL, blocks, lead_icon

PAGE = path_of('physical_invoice_list.html')
SRC, OLD = now(PAGE), was(PAGE)


def cell_of(text):
    i = text.index(CELL)
    a = text.index('>', i) + 1
    return text[a:text.find('</td>', a)]


# ==========================================================================
head('1. the order it was in, and the order it is in')

for label, text in (('was', OLD), ('now', SRC)):
    _pre, spans = blocks(cell_of(text))
    inner = cell_of(text)
    order = [lead_icon(inner[a:b]) for a, b in spans]
    print('      %-4s %s' % (label, ' -> '.join(x or '?' for x in order)))

_p, spans_old = blocks(cell_of(OLD))
io = cell_of(OLD)
old_order = [lead_icon(io[a:b]) for a, b in spans_old]
_p, spans_new = blocks(cell_of(SRC))
inew = cell_of(SRC)
new_order = [lead_icon(inew[a:b]) for a, b in spans_new]

ok(old_order != WANT, 'it really was out of house order', old_order)
ok(new_order == WANT, 'and reads LOOK, COPY, ADVANCE, DESTROY now', new_order)

# ==========================================================================
head('2. and the defect was one a person could see')

# The conditions each block is rendered under, read off the template.
CONDS = {
    'icon-approve': "row.status == 'draft'",
    'icon-send': "row.is_customer and row.status == 'approved'",
    'icon-duplicate': 'row.is_customer',
    'icon-delete': "row.status == 'draft'",
    'icon-pdf': '(always)',
}
for name, cond in CONDS.items():
    ok(cond == '(always)' or cond.split(' and ')[-1] in cell_of(SRC),
       '%-16s shows when %s' % (name, cond),
       'the condition is not in the cell - the reading below is stale')

# A DRAFT customer invoice, and an APPROVED one: four controls each.
draft = ['icon-pdf', 'icon-duplicate', 'icon-approve', 'icon-delete']
appr = ['icon-pdf', 'icon-duplicate', 'icon-send']
ok([x for x in new_order if x in draft] == draft,
   'a draft customer invoice reads %s' % ' -> '.join(draft))
ok([x for x in new_order if x in appr] == appr,
   'an approved one reads %s' % ' -> '.join(appr))
ok([x for x in old_order if x in draft] != draft,
   '  and neither did before, which is why this is not cosmetic',
   [x for x in old_order if x in draft])

# ==========================================================================
head('3. a permutation - not one character rewritten')

# STRIPPED, AND THE REASON IS NOT LAZINESS. The whitespace between two
# blocks rides with the one that follows, so when the order changes the
# indentation redistributes between the prefix and the blocks: the PDF
# block carried a leading newline when it was last and does not now that
# it is first. The CONTENT is untouched - 3612 characters in and 3612
# out - and that is what the next check guards. Comparing raw bytes here
# failed on a round that moved nothing but position.
a = sorted(io[x:y].strip() for x, y in spans_old)
b = sorted(inew[x:y].strip() for x, y in spans_new)
ok(a == b, 'the five blocks are what they were, character for character',
   'a block changed; this round only moves them')
ok(len(cell_of(OLD)) == len(cell_of(SRC)),
   '  and the cell is the same length - %d' % len(cell_of(SRC)))
for word in ('cannot be undone', 'Send this invoice now',
             'dated today', 'back to draft'):
    ok(word in cell_of(SRC), '  "%s" survived the move' % word)

# ==========================================================================
head('4. every control is still INSIDE the wrapper')

wraps = RA.wrappers(alv_tree.code_only(SRC))
held = max([len(RA.BTN_FULL.findall(w[2])) for w in wraps] or [0])
ok(held == len(WANT) + 1,
   'the wrapper holds all %d controls' % (len(WANT) + 1),
   'it holds %d - a tag moved with a block, which is exactly how the '
   'first build of this round shipped the PDF out of the group' % held)
ok(cell_of(SRC).count('row-actions') == 1,
   '  and there is still exactly one wrapper in the cell')
ok(cell_of(SRC).lstrip().startswith('<span class="row-actions">'),
   '  which still opens the cell, where RA-3b put it')

# ==========================================================================
head('5. the control - a block moved with the tag')

# Put the wrapper's opening tag inside the first block and move it: the
# shape the first build produced. Section 4 must catch it.
# OPEN THE WRAPPER LATE, so the controls before it fall outside. The
# first build of this round did the mirror image - it moved the opening
# tag along with the block it was glued to - and the effect is the same:
# a group with some of its members outside it.
bad = SRC.replace('<span class="row-actions">', '', 1)
# ANCHORED INSIDE THE CELL. The bare permission check appears earlier in
# the page too, and opening the wrapper THERE swallowed everything and
# still held six - the control passed while proving nothing. The
# duplicate block's condition is the first one inside this cell.
INSIDE = "{% if perms.auth.can_edit_invoices and row.is_customer %}"
bad = bad.replace(INSIDE, '<span class="row-actions">' + INSIDE, 1)
ok(bad != SRC, 'the control could be planted')
w2 = RA.wrappers(alv_tree.code_only(bad))
h2 = max([len(RA.BTN_FULL.findall(w[2])) for w in w2] or [0])
ok(h2 < len(WANT) + 1,
   '  and the check catches a wrapper that lost its group (%d held)' % h2,
   'it held %d - then section 4 would not have caught the first build' % h2)
ok(held == len(WANT) + 1, '  and the page itself is intact')

# ==========================================================================
head('6. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is in the push suites' % ME)

# ==========================================================================
print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
