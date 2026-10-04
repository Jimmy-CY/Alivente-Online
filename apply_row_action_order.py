# -*- coding: utf-8 -*-
"""RA-1 - A STANDARD ORDER FOR THE ACTION COLUMN

Demetri, 4 Oct 2026, of the Tenants list: "I think that we should put the
Delete Action Item on the right hand side of all the icons. We should
define a standard order that we place all icons in all tables, in the
Action Column and apply this across the app."

==========================================================================
THE ORDER, AGREED: LOOK -> CHANGE -> COPY -> ADVANCE -> DESTROY
==========================================================================
    LOOK     you are shown something and nothing happens
    CHANGE   this record is edited
    COPY     a new record is made from this one
    ADVANCE  the record moves on - sent, approved, locked, voided
    DESTROY  it is gone

Left to right the row gets more consequential, and the one thing that
cannot be undone sits at the end, furthest from the button pressed most.

Within LOOK, a second order: the record itself, then its papers, then its
children - view, document, list. Everything else sorts on the family
alone and STABLY, so a page that already reads sensibly is left exactly
as its author wrote it. This round decides where Delete goes; it does not
second-guess which of two Advance buttons a page meant to come first.

==========================================================================
THE CENSUS: 22 WRAPPERS, 5 OUT OF ORDER
==========================================================================
    meal_plan_calendar   view edit list duplicate delete
    meal_plans           view edit list duplicate delete
    properties           edit view view view
    suppliers            edit view delete
    tenant               edit delete view view       <- the one reported

The other seventeen already read Look-Change-Destroy and are not touched.
Demetri saw tenant, where Delete sits SECOND of four.

==========================================================================
.icon-view WAS CARRYING FOUR PICTURES
==========================================================================
base states the rule itself, three times, beside .icon-duplicate,
.icon-manage and .icon-list: "a class carries ONE PICTURE. Alias the
colour, never the name." It was not being kept:

    fa-eye            11   view this record
    fa-file-contract   3   View Lease Agreement, View Title Deed
    fa-box             1   View Property Assets
    fa-file-pdf        1   View receipt

Three new NAMES, one per picture: .icon-document (fa-file-contract),
.icon-pdf (fa-file-pdf) and .icon-assets (fa-box). Nothing is added to
the palette - all three point at --alv-view, which is the rule base
already wrote down three times: alias the colour, never the name.
Afterwards .icon-view draws fa-eye and nothing else.

AND NOT TWO OF THEM ON ONE NAME. The first build of this round put both
document glyphs on .icon-document and hung fa-box on the existing
.icon-list beside fa-shopping-cart - fixing a class that carried four
pictures by creating two that carried two. The suite asks the question
of EVERY class, which is how that was caught before it shipped.

AND IT IS NOT COSMETIC. The order sorts on the NAME, so a document
button wearing icon-view sorts as "view this record" and lands in the
wrong place inside LOOK. The split is what makes the rule expressible.

==========================================================================
HOW THE REORDER IS DONE: BLOCKS, NOT TEXT
==========================================================================
An action here is rarely one element. It is a permission test, the
control, and the disabled mirror a read-only user sees:

    {% if perms.auth.can_edit_tenants %}
      <a class="icon-action-btn icon-edit">...</a>
    {% else %}
      <span class="icon-action-btn icon-disabled">...</span>
    {% endif %}

and tenant's Delete is a whole <form> with a csrf token and an onsubmit
confirm in it. alv_rowactions splits a wrapper into balanced blocks and
sorts the BLOCKS; nothing inside one is rewritten, and the patcher
refuses unless the reordered text is the same bytes in a new order.

A BLOCK MAY HOLD MORE THAN ONE ACTION - crs/country_list writes Edit and
Delete inside a single {% if %} - and those cannot be separated by
sorting. alv_rowactions.unfixable() names any such pair that is out of
order; there are none today, and the suite fails if one appears.

Backups: .bak_rowactorder. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_rowactorder'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree
import alv_rowactions as RA

BASE = alv_tree.path_of('base.html')

# THE GLYPH DECIDES THE NAME, because the glyph is what the reader sees.
# ONE NAME PER PICTURE, WHICH IS WHAT THE RULE SAYS. The first build of
# this round put fa-file-contract and fa-file-pdf both on .icon-document
# and fa-box on the existing .icon-list beside fa-shopping-cart - and so
# created two NEW classes carrying two pictures each while fixing the one
# that carried four. Section 2 of the suite caught it: it asks the
# question of every class, not of .icon-view.
RECLASS = {
    'fa-file-contract': 'document',
    'fa-file-pdf': 'pdf',
    'fa-box': 'assets',
}


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
            raise SystemExit('RA1: %s is not a byte copy' % bak)


def swap(nl, old, new, what):
    c = nl.count(old)
    if c != 1:
        raise SystemExit('RA1: %s appears %d times, not once' % (what, c))
    return nl.replace(old, new)


print('=' * 74)
print('RA-1 - LOOK, CHANGE, COPY, ADVANCE, DESTROY%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. base GAINS .icon-document AND WRITES THE ORDER DOWN.
# ==========================================================================
t, raw = read(BASE)
nl = t.replace('\r\n', '\n')

CSS = """
      /* Document: the SIXTH NAME on --alv-view, added by RA-1 on 4 Oct 2026.
   .icon-view was carrying FOUR pictures - fa-eye eleven times, but also
   fa-file-contract on View Lease Agreement and View Title Deed, fa-box
   on View Property Assets and fa-file-pdf on View receipt. base states
   the rule beside .icon-duplicate, .icon-manage and .icon-list and it
   was simply not being kept: A CLASS CARRIES ONE PICTURE. Alias the
   colour, never the name.

   Opening the paper a record refers to is still a LOOK, so it points at
   --alv-view like the eye. It takes its own name because the row-action
   ORDER sorts on the NAME: a lease agreement wearing .icon-view sorts as
   "view this record" and lands in the wrong place inside Look. The split
   is what makes the standard expressible, not decoration.

   THREE NAMES, ONE PER PICTURE. .icon-pdf and .icon-assets are here for
   the same reason .icon-document is, and for no other: fa-file-pdf is
   not fa-file-contract, and a property's assets are not a shopping
   list. The first build of this round economised - both document
   glyphs on .icon-document, fa-box on the existing .icon-list - and
   repaired a class carrying four pictures by making two that carried
   two. All three point at --alv-view and the palette is unchanged.

   THE ORDER ITSELF - LOOK, CHANGE, COPY, ADVANCE, DESTROY - is in
   alv_rowactions.py, shared by the patcher, Show-RowActionDrift.py and
   test_row_action_order.py so that it is written once.
                                       [test_row_action_order.py] */
      .icon-document,
      .icon-pdf,
      .icon-assets       { color: var(--alv-view); border-color: var(--alv-accent-line); }
      .icon-document:hover,
      .icon-pdf:hover,
      .icon-assets:hover { background: var(--alv-view); border-color: var(--alv-view); color: var(--alv-on-accent); }
      .icon-color-document,
      .icon-color-pdf,
      .icon-color-assets { color: var(--alv-view); }
"""

if 'RA-1 on 4 Oct 2026' in nl:
    print('  base.html                  already defines .icon-document')
else:
    if '.icon-document' in nl:
        raise SystemExit('RA1: base.html already names .icon-document')
    # BESIDE .icon-upload, NOT WITH THE LATER NAMES. Two reasons, and
    # the second is the one that was measured. First, this is where base
    # states the precedent these three follow - "a new action takes its
    # own NAME on an EXISTING colour, never a seventh tone" - so the
    # rule and its reasoning sit together. Second, base has four <style>
    # blocks and probes elsewhere in the tree pull only the ones holding
    # the tokens: test_table_lease_agreement renders with the blocks
    # that define --alv-accent or --alv-paper, and the first build of
    # this round put these three in a block with neither. .icon-document
    # then resolved to nothing in that probe, fell through to
    # .icon-action-btn's --alv-ink-soft, and the lease agreement
    # measured grey. A rule in the wrong block is a rule some of this
    # tree cannot see.
    nl = swap(nl,
              "      .icon-upload:hover { background: var(--alv-edit); "
              "border-color: var(--alv-edit); color: #fff; }\n",
              "      .icon-upload:hover { background: var(--alv-edit); "
              "border-color: var(--alv-edit); color: #fff; }\n" + CSS,
              "the icon-upload terminator")
    out = nl.replace('\n', '\r\n') if CRLF.get(BASE) else nl
    if not CHECK:
        back_up(BASE, raw)
        write(BASE, out)
    print('  base.html                  3 NAMES on --alv-view, one per picture')

# ==========================================================================
# 2. EVERY ROW-ACTION WRAPPER: RECLASS BY GLYPH, THEN SORT THE BLOCKS.
# ==========================================================================
# ASKED OF THE TREE, NOT OF A LIST TYPED HERE. The five pages that need
# reordering are named in the docstring for the reader; they are not the
# input, so a sixth that drifts in tomorrow is handled by the same pass.
BTN_RE = re.compile(
    r'(<(?:a|button|span)\b[^>]*class=")([^"]*\bicon-action-btn\b[^"]*)'
    r'("[^>]*>\s*<i class="[^"]*?)(fa-[a-z0-9-]+)', re.S)


def reclass(inner):
    """Rename a control's icon-* class to match the picture it draws."""
    def one(m):
        cls, glyph = m.group(2), m.group(4)
        want = RECLASS.get(glyph)
        if not want:
            return m.group(0)
        parts = cls.split()
        # The DISABLED MIRROR keeps icon-disabled and gains nothing: it
        # is already classed by what it is, and its glyph is what sorts
        # it. Only a live control is renamed.
        if 'icon-disabled' in parts:
            return m.group(0)
        parts = ['icon-' + want if p == 'icon-view' else p for p in parts]
        return m.group(1) + ' '.join(parts) + m.group(3) + m.group(4)
    return BTN_RE.sub(one, inner)


touched = []
for p in sorted(alv_tree.templates()):
    name = alv_tree.rel(p).replace(os.sep, '/')
    txt, praw = read(p)
    nlp = txt.replace('\r\n', '\n')
    if 'RA-1, 4 Oct 2026' in nlp:
        continue
    out = nlp
    moved = renamed = 0
    # LAST WRAPPER FIRST, so an earlier edit does not shift the offsets
    # of a later one.
    for s, e, inner in reversed(RA.wrappers(alv_tree.code_only(nlp))):
        # The offsets come from code_only'd text, which is the same
        # LENGTH as the original - code_only blanks, it does not delete -
        # so they index the real file.
        real = out[s:e]
        new = reclass(real)
        if new != real:
            renamed += 1
        nxt = RA.ordered(new)
        if sorted(nxt.split()) != sorted(new.split()):
            raise SystemExit('RA1: %s - reordering changed the bytes' % name)
        if nxt != new:
            moved += 1
        out = out[:s] + nxt + out[e:]
    if out == nlp:
        continue
    # A NOTE ON THE PAGE, so the next reader knows the order is a rule.
    first = RA.OPEN.search(out)
    note = ('{# RA-1, 4 Oct 2026 - the action column is in house order:  #}\n'
            '{# LOOK, CHANGE, COPY, ADVANCE, DESTROY. Delete is last on  #}\n'
            '{# every table in the app. alv_rowactions.py holds the rule #}\n'
            '{# and Show-RowActionDrift reports any row that leaves it.  #}\n')
    line_start = out.rfind('\n', 0, first.start()) + 1
    indent = out[line_start:first.start()]
    out = (out[:line_start]
           + ''.join(indent + l + '\n' for l in note.strip().split('\n'))
           + out[line_start:])
    res = out.replace('\n', '\r\n') if CRLF.get(p) else out
    if not CHECK:
        back_up(p, praw)
        write(p, res)
    touched.append((name, moved, renamed))

for name, moved, renamed in touched:
    print('  %-42s %d reordered, %d reclassed' % (name, moved, renamed))
if not touched:
    print('  every wrapper in the tree               already in house order')

# ==========================================================================
# 3. THE SUITE THAT NAMED A CLASS THIS ROUND RENAMED.
# ==========================================================================
# test_table_lease_agreement builds its probe by taking the page's own
# row and switching ONE of its buttons to the else-branch class, so the
# disabled state is measured on real markup rather than on a span this
# file wrote. It switched `icon-action-btn icon-view`, and the button it
# meant is View Lease Agreement - which is a DOCUMENT now, so the
# replace matched nothing and the probe rendered with neither an
# .icon-view nor an .icon-disabled in it.
#
# Its claim was true and is still true; the class it names has moved.
# The round that moved it owes the repair.
REPAIRS = [
    ('test_table_lease_agreement.py',
     """            r = (r.replace('icon-action-btn icon-view',
                           'icon-action-btn icon-disabled', 1)""",
     """            # RA-1, 4 Oct 2026 - icon-document, not icon-view. This
            # page's only Look button opens the lease agreement itself,
            # and .icon-view had been carrying four different pictures.
            # Switching a class that is no longer in the markup leaves
            # the probe with no disabled button at all - and then four
            # checks measure nothing and say so, which is the fixture
            # working.
            r = (r.replace('icon-action-btn icon-document',
                           'icon-action-btn icon-disabled', 1)"""),
    ('test_table_lease_agreement.py',
     """            vw = cs(pg, '.icon-view', ['color'])
            check('desktop: View is the accent teal (%s)' % vw['color'],
                  vw['color'] == 'rgb(14, 124, 139)')""",
     """            # RA-1 - the same button, under the name it wears now.
            # .icon-document is a NAME on --alv-view, so the colour it
            # has to measure is unchanged: that is the point of aliasing
            # the colour and never the name.
            vw = cs(pg, '.icon-document', ['color'])
            check('desktop: the lease agreement is the accent teal (%s)'
                  % vw['color'], vw['color'] == 'rgb(14, 124, 139)')"""),
    ('test_table_lease_agreement.py',
     """for sel in ('.icon-action-btn', '.icon-edit', '.icon-view', '.icon-delete',""",
     """for sel in ('.icon-action-btn', '.icon-edit', '.icon-view', '.icon-document',
            '.icon-delete',"""),
]

for name, old_t, new_t in REPAIRS:
    path = os.path.join(ROOT, name)
    if not os.path.isfile(path):
        print('  %-42s not on disk - skipped' % name)
        continue
    t2, raw2 = read(path)
    n2 = t2.replace('\r\n', '\n')
    if new_t.strip().split('\n')[0] in n2:
        print('  %-42s already repaired' % name)
        continue
    c = n2.count(old_t)
    if c != 1:
        raise SystemExit('RA1: %s - the claim to repair appears %d times, '
                         'not once' % (name, c))
    n2 = n2.replace(old_t, new_t)
    out2 = n2.replace('\n', '\r\n') if CRLF.get(path) else n2
    if not CHECK:
        back_up(path, raw2)
        write(path, out2)
    print('  %-42s claim follows the rename' % name)

print('=' * 74)
print('RA-1 %s' % ('would apply' if CHECK else 'applied'))
print('=' * 74)
