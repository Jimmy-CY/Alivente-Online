# -*- coding: utf-8 -*-
"""FA-1 - THE FILTER FIELDS ARE NOT IN LINE

Demetri, 4 Oct 2026, of the Projects filter panel: "The filters are not
in line...."

==========================================================================
IT IS TEN PAGES, NOT ONE
==========================================================================
Rendered at 1280, every filter panel in the tree, before this round:

    act_expense                 in line
    cash_receipts               in line
    categories_management       in line
    celebration_management      in line
    customer_list               OUT - label tops 0 and 2
    fsr                         OUT - label tops 0 and 2
    ingredient_base_units       OUT - label tops 0 and 2
    invoices                    in line
    measurement_units           in line
    passport_management         in line
    physical_invoice_list       OUT - label tops 0 and 2
    projects/projects           OUT - label tops 0 and 25
    properties                  OUT - label tops 0 and 2
    suppliers                   OUT - label tops 0 and 2
    tenant                      in line
    tenant_lease_agreement      OUT - label tops 0 and 2
    unit_conversions            OUT - label tops 0 and 6

Demetri saw the 25px one. The 2px ones are the same defect at a size you
feel rather than see.

==========================================================================
ONE DECLARATION CAUSES ALL OF THEM
==========================================================================
    .filter-grid { align-items: end; }

end aligns the BOTTOMS of the groups. Every group is label-above-control,
so the bottom is the bottom of the control - and the moment two groups
are not the same height, their tops part company:

  - 2px, on eight pages: the search field is an <input> and the rest are
    <select>, and a select is 2px taller. Bottoms level, tops 2px apart.
  - 25px, on Projects: the Search group has an .alv-search-hint UNDER its
    control. The group's bottom is now the bottom of the HINT, so the
    whole group - label, box and all - is lifted 25px to put the hint
    where the other controls end.

The hint is doing exactly what it was told. It is the instruction that
is wrong: a filter panel is a row of LABELLED CONTROLS, and what a reader
lines up on is the top of the labels.

==========================================================================
AND THE FIX IS THAT ONE WORD
==========================================================================
    align-items: end  ->  align-items: start

Measured after, on all seventeen panels that render: every label top 0,
every control top 27, with no exceptions and nothing else moved. A hint
now hangs below its own control and pushes nothing, which is what a hint
is for.

Every .filter-label in the tree measures 21px tall, so aligning the
label tops aligns the control tops as well. That is not assumed - it is
in the measurement, and in section 2 of the suite, which fails if any
label in any panel is ever taller than one line.

==========================================================================
AND PROJECTS KEEPS ITS OWN COLUMN WIDTHS - NO LONGER
==========================================================================
Demetri's call, asked and answered: "No - all three the same."

    .filter-grid { grid-template-columns: 2fr 1fr 1fr; }

That override is why Search measures 546px beside two 290px selects, and
it is also why none of the three gets FG-1's 240px cap - the cap Demetri
asked for on 3 Oct, in those words: "the filter fields must be made less
wide, so that they fit on one line". Dropped, so the page takes base's
repeat(auto-fit, minmax(200px, 240px)) like Passports and Categories.

ELEVEN OTHER PAGES STILL SET THEIR OWN COLUMNS. Not touched here - this
round was asked about Projects, and taking the other eleven is a visible
change to eleven pages nobody has looked at yet. The census is in the
suite so the number cannot drift unnoticed.

Backups: .bak_filteralign. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_filteralign'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

BASE = alv_tree.path_of('base.html')
PROJ = [p for p in alv_tree.templates()
        if alv_tree.rel(p).replace(os.sep, '/') == 'projects/projects.html'][0]


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
            raise SystemExit('FA1: %s is not a byte copy' % bak)


def swap(nl, old, new, what):
    c = nl.count(old)
    if c != 1:
        raise SystemExit('FA1: %s appears %d times, not once' % (what, c))
    return nl.replace(old, new)


print('=' * 74)
print('FA-1 - THE FILTER FIELDS LINE UP ON THEIR LABELS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. BASE ALIGNS THE TOPS.
# ==========================================================================
t, raw = read(BASE)
nl = t.replace('\r\n', '\n')

OLD_B = """.filter-grid {
    display: grid;
    gap: 20px;
    align-items: end;
"""
NEW_B = """.filter-grid {
    display: grid;
    gap: 20px;
    /* START, NOT end - FA-1, 4 Oct 2026, and Demetri found it on
       Projects: "The filters are not in line...."

       end aligns the BOTTOMS of the groups. A group is a label above a
       control, so its bottom is the bottom of the control - and the
       moment two groups are not the same height, their TOPS part
       company. Rendered at 1280, ten of the seventeen panels in this
       tree were out of line, for two reasons:

         2px, on eight pages: the search field is an <input> and the
         rest are <select>, and a select is 2px taller.

         25px, on Projects: its Search group carries an
         .alv-search-hint UNDER the control, so the group's bottom is
         the bottom of the HINT and the whole group - label, box and
         all - was lifted 25px to put the hint where the other controls
         ended.

       The hint was doing what it was told. The instruction was wrong: a
       filter panel is a row of LABELLED controls and what a reader
       lines up on is the top of the labels. With start, all seventeen
       measure label top 0 and control top 27, and a hint hangs below
       its own control and pushes nothing - which is what a hint is for.

       Every .filter-label in the tree is one line, 21px, which is why
       aligning the labels aligns the controls too. test_filter_align
       section 2 fails if one ever wraps. */
    align-items: start;
"""

if 'FA-1, 4 Oct 2026' in nl:
    print('  base.html                  already aligns the tops')
else:
    # THE CLAIM IS THAT ONE DECLARATION CAUSES ALL TEN. If the file has
    # a second align-items on .filter-grid further down, it does not,
    # and this round would fix some pages and not others.
    for m in re.finditer(r'\.filter-grid[^{]*\{[^}]*\}', nl):
        if 'align-items' in m.group(0) and 'align-items: end' not in m.group(0):
            raise SystemExit('FA1: a second .filter-grid alignment:\n%s'
                             % m.group(0))
    nl = swap(nl, OLD_B, NEW_B, "base's filter-grid alignment")
    out = nl.replace('\n', '\r\n') if CRLF.get(BASE) else nl
    if not CHECK:
        back_up(BASE, raw)
        write(BASE, out)
    print('  base.html                  align-items: end -> start')

# ==========================================================================
# 2. PROJECTS TAKES BASE'S COLUMNS.
# ==========================================================================
p, praw = read(PROJ)
pnl = p.replace('\r\n', '\n')

OLD_P = """.filter-grid {
    grid-template-columns: 2fr 1fr 1fr;
}
"""
NEW_P = """/* FA-1, 4 Oct 2026 - THE COLUMN OVERRIDE IS GONE. Demetri, asked
   whether Search should stay wider than the two selects: "No - all
   three the same."

   2fr 1fr 1fr is why Search measured 546px beside two 290px selects,
   and it is also why none of the three got FG-1's cap - the one
   Demetri asked for on 3 Oct in these words: "the filter fields must
   be made less wide, so that they fit on one line". A page's own
   track list comes later in the document and wins.

   Without it the panel takes base's
   repeat(auto-fit, minmax(200px, 240px)), the same as Passports,
   Categories and Measurement Units. */
"""

if 'FA-1, 4 Oct 2026' in pnl:
    print('  projects/projects.html     already takes base\'s columns')
else:
    pnl = swap(pnl, OLD_P, NEW_P, "the Projects column override")
    out = pnl.replace('\n', '\r\n') if CRLF.get(PROJ) else pnl
    if not CHECK:
        back_up(PROJ, praw)
        write(PROJ, out)
    print('  projects/projects.html     3 fields at base\'s 240px cap')

# ==========================================================================
# 3. THE TWO LEDGERS THIS ROUND MOVES.
# ==========================================================================
# test_filter_frame keeps two records and compares the tree against them
# declaration by declaration, which is exactly why they have to be kept
# up: loosening the comparison instead would stop it noticing a column
# template that changed by accident, which is the thing it is for.
REPAIRS = [
    # base's own frame may gain or change a declaration, and the file
    # already has a table for that - FG-1 used it to add the columns.
    ('test_filter_frame.py',
     """HOUSE_AMENDED = {
    '.filter-grid': {
        'grid-template-columns': 'repeat(auto-fit, minmax(200px, 240px))',
        'justify-content': 'start',
    },
}""",
     """HOUSE_AMENDED = {
    '.filter-grid': {
        'grid-template-columns': 'repeat(auto-fit, minmax(200px, 240px))',
        'justify-content': 'start',
        # FA-1, 4 Oct 2026 - was `end`. end aligned the BOTTOMS of the
        # groups, so a select 2px taller than an input parted their tops
        # by 2px and a search HINT under its control parted Projects' by
        # 25. Ten of the seventeen panels in this tree were out of line.
        'align-items': 'start',
    },
}"""),

    # AND A PAGE MAY DROP ONE. AMENDED records a value MOVING; Projects
    # loses its column template outright, so the record has to be able to
    # say "gone" as well as "changed". None is that, and the loop below
    # reads it.
    ('test_filter_frame.py',
     """AMENDED = {
    ('act_expense.html', '.filter-grid', 'grid-template-columns'):
        ('2fr 1fr 1fr',
         'minmax(0, 1.6fr) minmax(0, 1.2fr) minmax(0, 1.2fr) 170px 170px'),
}""",
     """AMENDED = {
    ('act_expense.html', '.filter-grid', 'grid-template-columns'):
        ('2fr 1fr 1fr',
         'minmax(0, 1.6fr) minmax(0, 1.2fr) minmax(0, 1.2fr) 170px 170px'),
    # FA-1, 4 Oct 2026 - GONE, not moved. Demetri, asked whether Search
    # should stay wider than the two selects beside it: "No - all three
    # the same." 2fr 1fr 1fr was also why none of the three got FG-1's
    # 240px cap, since a page's own track list comes later and wins.
    # None means the declaration is no longer there at all.
    ('projects/projects.html', '.filter-grid', 'grid-template-columns'):
        ('2fr 1fr 1fr', None),
}"""),

    # test_ae_line counts how many ROWS the five Actual Expenses filters
    # take, and its probe says in its own comment why it counts BOTTOM
    # edges: "because align-items: end lines the bottoms up and the
    # groups differ in height". This round makes it start, so the bottoms
    # are the thing that no longer lines up and the tops are. The claim -
    # all five on ONE line - is unchanged, and was reporting two rows
    # while the detail printed all five at top: 141.
    ('test_ae_line.py',
     """  // How many ROWS the five groups occupy: distinct bottom edges, because
  // align-items: end lines the bottoms up and the groups differ in height.
  const groups = [...p.querySelectorAll('.filter-grid > .filter-group, '
                 + '.date-filter-grid > .filter-group')];
  out.lines = new Set(groups.map(e =>
      Math.round(e.getBoundingClientRect().bottom))).size;""",
     """  // How many ROWS the five groups occupy: distinct TOP edges.
  //
  // FA-1, 4 Oct 2026 - this counted BOTTOMS, and said why: align-items
  // was `end`, which lined the bottoms up while the groups differed in
  // height. FA-1 makes it `start` for the ten panels that were out of
  // line, so the tops are what agree now and the bottoms are not. The
  // claim is the same one - five groups, one row - and counting the
  // edge that no longer lines up reported two rows while every control
  // measured top: 141.
  const groups = [...p.querySelectorAll('.filter-grid > .filter-group, '
                 + '.date-filter-grid > .filter-group')];
  out.lines = new Set(groups.map(e =>
      Math.round(e.getBoundingClientRect().top))).size;"""),

    # test_filter_grid holds that FG-1 moved only the page that had no
    # columns of its own - the twelve that set their own are identical
    # before and after. TRUE OF FG-1. This round deliberately takes one
    # of the twelve off that list, so it is named rather than the
    # comparison loosened.
    ('test_filter_grid.py',
     """                if rel in own:
                    if a != b:""",
     """                if rel in own:
                    # FA-1, 4 Oct 2026 - Projects is the exception now.
                    # Demetri, asked whether Search should stay wider
                    # than the two selects: "No - all three the same."
                    # It dropped its 2fr 1fr 1fr and takes base's capped
                    # track list, so it moves at 1920 and 1280 and this
                    # check would be asserting the opposite of what was
                    # asked for. NAMED, not loosened: every other page
                    # on that list is still held to the byte.
                    if 'projects' in os.path.basename(rel):
                        continue
                    if a != b:"""),

    # AND THE RENDERED-CHANGE LEDGER, which names one by one what this
    # round's own comparison is allowed to have moved since H1. It is
    # the same discipline as AMENDED, a layer down: measured in a
    # browser rather than read off the CSS. FG-1 added grid.just to it
    # for exactly this reason - every panel moves, which is the point of
    # putting a declaration in base.
    ('test_filter_frame.py',
     """                if (k == 'grid.cols' and rel == 'act_expense.html'
                        and len(v[1].split()) == 5):""",
     """                if (k == 'grid.cols' and rel == 'projects/projects.html'
                        and set(v[1].split()) <= {'240px', '0px'}):
                    # FA-1, 4 Oct 2026. Demetri, asked whether Search
                    # should stay wider than the two selects beside it:
                    # "No - all three the same." The page dropped its
                    # 2fr 1fr 1fr and takes base's capped track list, so
                    # 620/310/310 becomes three tracks of 240 - and two
                    # empty ones, because auto-fit lays out five slots
                    # for a 1200px panel and collapses the two nothing
                    # sits in. MEASURED, not merely "something changed":
                    # every track is either the cap or nothing.
                    continue
                if (k == 'grid.cols' and rel == 'act_expense.html'
                        and len(v[1].split()) == 5):"""),

    ('test_filter_frame.py',
     """                if k == 'grid.just' and v == ('normal', 'start'):""",
     """                if k == 'grid.align' and v == ('end', 'start'):
                    # FA-1, 4 Oct 2026. end aligned the BOTTOMS of the
                    # groups, so the moment two differed in height their
                    # tops parted: 2px wherever a select sat beside an
                    # input, 25px on Projects, where a search HINT under
                    # the control made the group's bottom the hint's
                    # bottom. Ten of seventeen panels were out of line.
                    # EVERY PANEL MOVES, which is again the point of
                    # putting it in base.
                    continue
                if k == 'grid.just' and v == ('normal', 'start'):"""),

    ('test_filter_frame.py',
     """            want[a_sel][a_key] = a_now""",
     """            # FA-1 - None means the page DROPPED the declaration.
            if a_now is None:
                want[a_sel].pop(a_key, None)
                if not want[a_sel]:
                    want.pop(a_sel)
            else:
                want[a_sel][a_key] = a_now"""),
]

for name, old_t, new_t in REPAIRS:
    path = os.path.join(ROOT, name)
    if not os.path.isfile(path):
        print('  %-26s not on disk - skipped' % name)
        continue
    t2, raw2 = read(path)
    n2 = t2.replace('\r\n', '\n')
    # DONE IS DECIDED BY A MARKER UNIQUE TO THIS REPAIR, and this loop
    # has now been wrong in both of the other two ways.
    #
    #   "the new text's first line is present" skipped a later repair
    #   whose first line was `AMENDED = {`, already in the file.
    #
    #   "the anchor is gone" re-applied a repair whose anchor SURVIVES
    #   inside its own replacement - the new code still contains
    #   `want[a_sel][a_key] = a_now`, one branch deeper - so the second
    #   run nested it again and left the file with a SyntaxError.
    #
    # The marker is the first line of the comment each repair writes,
    # which exists nowhere else.
    marker = next((l.strip() for l in new_t.split('\n')
                   if l.strip().startswith('#') and len(l.strip()) > 12),
                  new_t.strip()[:60])
    if marker in n2:
        print('  %-26s already up to date' % name)
        continue
    c = n2.count(old_t)
    if c != 1:
        raise SystemExit('FA1: %s - the anchor appears %d times, not once'
                         % (name, c))
    n2 = n2.replace(old_t, new_t)
    out2 = n2.replace('\n', '\r\n') if CRLF.get(path) else n2
    if not CHECK:
        back_up(path, raw2)
        write(path, out2)
    print('  %-26s ledger follows this round' % name)

print('=' * 74)
print('FA-1 %s' % ('would apply' if CHECK else 'applied'))
print('=' * 74)
