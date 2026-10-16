# -*- coding: utf-8 -*-
"""apply_deed_table.py - round NV-1b, 16 Oct 2026.

THE LAST HAND-ROLLED TABLE ON A SERVER-RENDERED PAGE.

Demetri, after a full check of the Administration module:

  "Why does the Upload Titel Dees table not resemble our standards."

Because it does not wear them. The table is

    class="table table-bordered table-striped text-center title-deeds-table"

with no house class at all, and the page hand-rolls, in its own
stylesheet, the entire phone card block that `.alv-table` has owned
since the table standard landed.


FIFTEEN RULE OPENINGS GO, AND TWELVE OF THEM ARE BASE'S JOB     MEASURED
============================================================================
base, in its max-width: 768px block, already declares every one of
these - and more of them than the page did:

    .alv-table                          border none, transparent
    .alv-table thead                    display: none
    .alv-table, tbody, tfoot, tr, td    display: block; width: 100%
    .alv-table tbody tr                 the card: paper, line, radius
      + .table-striped odd AND even     the stripe override
      + tbody tr:hover                  which the page never had
    .alv-table td                       border none, padding, flex row
    .alv-table td::before               content: attr(data-label)
    .alv-table tbody td:first-child     16px, 600, the prominence
    .alv-table tbody td:first-child::before   content: none
    .desktop-action-cell                display: none
    .mobile-action-bar  + ::before      the grid, and its label suppressed

THE FIRST-CELL PAIR IS THE ONE WORTH NAMING. The page writes them as
`td[data-label="Property"]` and `::before` - first-cell prominence with
its own label suppressed - and base does the same thing BY POSITION,
for every converted table. Same cell, same declarations.

THREE OF THEM ARE NOT BYTE-IDENTICAL, AND THIS ROUND SAYS SO RATHER
THAN CALLING THEM DUPLICATES:

    the card shadow   0 2px 4px rgba(0,0,0,.04)   ->  0 1px 2px rgba(16,34,40,.05)
    the cell label    --alv-ink-strong at 13px    ->  --alv-ink-soft at 12.5px
    the cell          (no flex-wrap)              ->  flex-wrap: wrap

The radius is the same number by two spellings - the page says 8px and
base says var(--alv-radius), which IS 8px. The other three are the house
values replacing page-local ones, which is the whole point of the round,
and the suite MEASURES each of them before and after rather than
asserting that nothing moved.

The three that go from the top level are the page's desktop hide for
`.mobile-action-bar` and its two status spans.


THE BAR'S COLUMN COUNT IS NOT A DUPLICATE AND IS NOT KEPT
============================================================================
    page   .mobile-action-bar { grid-template-columns: 1fr 1fr; }
    base   .mobile-action-bar { grid-template-columns: repeat(3, 1fr); }

This page has TWO mobile actions, so deleting its rule as a duplicate
would lay two buttons across two of three columns. It is not kept
either: base already carries the opt-in -

    .mobile-action-bar.cols-2 { grid-template-columns: repeat(2, 1fr); }

- so the markup takes `cols-2` and the hand-rolled copy goes. A rule
written out by hand where an OPT-IN exists is the same defect as a rule
written out by hand where base has the default; it just looks less like
one.


AND THE PAGE MUST NOT DECLARE .mobile-action-bar AT ALL        MEASURED
============================================================================
THE FIRST CUT OF THIS ROUND HID THE ACTION BAR ON EVERY PHONE, and only
the render said so.

The page declares `.mobile-action-bar { display: none !important }` at
top level - its desktop hide - and un-hides it inside its own 768px
block. base declares exactly the same pair. Deleting only the phone copy
as a duplicate leaves the page's top-level hide standing, and the page's
stylesheet loads AFTER base, so on source order that `display: none
!important` beats base's phone `display: grid !important`. The deed
actions vanish on a phone entirely.

So both halves go together, and the patcher REFUSES if any declaration
of `.mobile-action-bar` survives on the page. A bar that vanished on a
phone is the one thing Demetri checks every round.


THE STATUS CELL JOINS THE HOUSE VOCABULARY
============================================================================
`.status-uploaded` and `.status-missing` are two page-local spans where
every other table's Status column is an `.alv-pill`. They become
`alv-pill-good` and `alv-pill-neutral` - NEUTRAL and not BAD, because a
property with no title deed uploaded yet is a STATE and not a fault,
which is what the rule it replaces already said in its own way:
`color: --alv-ink-soft; font-style: italic`.

Both rules then have no element and go with the markup.


AND THE PART HE ACTUALLY SAW
============================================================================
The Actions cell draws `btn btn-sm btn-danger` and
`btn btn-sm btn-outline-primary` - two Bootstrap buttons in a column
where the whole application draws `icon-action-btn` inside
`.row-actions`. Those become `icon-delete` and `icon-upload`, which are
already in the row-action vocabulary: upload is ADVANCE (3) and delete
is DESTROY (4), so alv_rowactions is what puts them in that order
rather than the markup.

THE TABLE TAG TAKES THE HOUSE SPELLING. `table alv-table`, which is how
all 28 converted tables spell it. `table-bordered` and `table-striped`
go because base NEUTRALISES both on `.alv-table` - border: 0 and both
nth-of-type stripes transparent - so they are three classes that change
nothing. `text-center` goes to the three columns that want it:
`col-center` on the heads, and the body cells keep their centring from
`.alv-table .desktop-action-cell` and one `text-center` on Status.

AND `title-deeds-table` GOES WITH THEM. Every rule naming it is one of
the twelve this round deletes; the column widths are inline on the
`<th>`s. A class whose last rule has just been removed is dead weight,
and renaming or keeping a dead name is CC-1's line from 15 Oct: a rule
with no element is dead weight exactly as an element with no rule is a
bug.


WHAT THIS ROUND DOES NOT TOUCH, AND WHY IT IS WORTH SAYING
============================================================================
test_table_admin.py is titled "the last two hand-rolled tables", and
that was true of what its census could see. Searching the whole tree for
the signature - a `thead { display: none }` beside an
`attr(data-label)` - finds this page and FIFTEEN MORE tables, on
home.html and notifications.html, built in JavaScript as
`class="data-table"`. `data-table` was never in the table vocabulary, so
no table suite in this project can see any of them. Banked as DT-1. Same
shape as VB-1's recipe overlay: a census that cannot see a thing reports
nought.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_deedtable'
PAGE = 'title_deeds_management.html'
ME = 'test_deed_table.py'
PATCHER = 'apply_deed_table.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
BH = 'test_bar_height.py'
IB = 'test_important_base.py'
PL = 'test_print_leaks.py'
CHECK = False

# THE TREE'S !important CENSUS. Twelve of the fifteen rule openings this
# round removes carried !important - the page's own phone card block
# wrote `border: none !important`, `padding: 6px 0 !important`,
# `text-align: left !important` and the rest, every one of them a copy
# of a declaration base already makes. title_deeds_management goes from
# 14 to 1. Measured with cs1_census.count_important, per page, not
# reasoned about.
IMP_WAS, IMP_NOW = 855, 842

# THE MARKUP CENSUS SEES TWO CONTROLS IT COULD NOT SEE BEFORE. The
# Actions cell drew `btn btn-sm btn-danger` and `btn btn-sm
# btn-outline-primary`, and test_bar_height selects
# .action-primary/-secondary/-back/-filter/-more-btn/.icon-action-btn -
# so two Bootstrap buttons became two house icon buttons and the table
# row count rises by exactly two. Measured per page against this
# round's own backup, not reasoned about.
ROW_WAS_N, ROW_NOW_N = 110, 112

CONVERTED_WAS, CONVERTED_NOW = 85, 86
ALIAS_WAS, ALIAS_NOW = 81, 83
ALIAS_P_WAS, ALIAS_S_WAS = 40, 41
ALIAS_P_NOW, ALIAS_S_NOW = 41, 42

N_RULES_OUT = 15
DEAD_CLASS = 'title-deeds-table'

# The twelve inside the phone block, named by selector so the anchor is
# EXTRACTED from the file with brace matching rather than transcribed.
# The eight-trailing-spaces line inside .mobile-action-bar is why: an
# anchor typed by hand missed on whitespace nobody can see, and spelling
# it out in the source only moves the problem.
PHONE_OUT = [
    '.title-deeds-table',
    '.title-deeds-table thead',
    '.title-deeds-table,\n    .title-deeds-table tbody,\n'
    '    .title-deeds-table tr,\n    .title-deeds-table td',
    '.title-deeds-table tbody tr',
    '.title-deeds-table tbody tr:nth-of-type(even)',
    '.title-deeds-table td',
    '.title-deeds-table td::before',
    '.title-deeds-table td[data-label="Property"]',
    '.title-deeds-table td[data-label="Property"]::before',
    '.desktop-action-cell',
    '.mobile-action-bar',
    '.mobile-action-bar::before',
]

# And the three at the top level.
TOP_OUT = [
    '.mobile-action-bar',
    '.status-uploaded',
    '.status-missing',
]

NOTE = """/* NV-1b, 16 Oct 2026 - THE PHONE CARD BLOCK IS BASE'S, NOT THIS PAGE'S.
   Demetri: why does the Upload Title Deeds table not resemble our
   standards. Because it did not wear them - no .alv-table at all, and
   fifteen rule openings in this stylesheet re-declaring what base has
   owned since the table standard landed.

   TWELVE WERE BASE'S JOB and are gone. Three of those twelve were not
   byte-identical and the house value wins: the card shadow is
   0 1px 2px rgba(16,34,40,.05) rather than 0 2px 4px rgba(0,0,0,.04),
   the cell label is --alv-ink-soft at 12.5px rather than
   --alv-ink-strong at 13px, and the cell gains flex-wrap. The radius
   was the same 8px under two spellings.

   .mobile-action-bar IS NOT DECLARED HERE ANY MORE, in either place,
   and the patcher refuses if it comes back. This page's top-level
   `display: none !important` loads after base and beats base's phone
   `display: grid !important` on source order - so deleting only the
   phone copy hid the action bar on every phone. Nothing but the render
   said so.

   The bar asks for its two columns with base's `cols-2` opt-in. A rule
   written by hand where an opt-in exists is the same defect as one
   written by hand where base has the default. */"""

# ---------------------------------------------------------------- markup
TABLE_WAS = """<table class="table table-bordered table-striped text-center title-deeds-table">
<thead>
    <tr>
        <th style="text-align: left; width: 35%">Property Name</th>
        <th style="text-align: left; width: 25%">Country</th>
        <th style="width: 15%">Status</th>
        <th style="width: 15%">Title Deed</th>
        <th style="width: 10%">Actions</th>
    </tr>
</thead>"""

TABLE_NOW = """<table class="table alv-table">
<thead>
    <tr>
        <th style="width: 35%">Property Name</th>
        <th style="width: 25%">Country</th>
        <th class="col-center" style="width: 15%">Status</th>
        <th class="col-center" style="width: 15%">Title Deed</th>
        <th class="col-center" style="width: 10%">Actions</th>
    </tr>
</thead>"""

CELLS_WAS = """        <td data-label="Property" style="text-align: left">{{ property.prop_name }}</td>
        <td data-label="Country" style="text-align: left">{{ property.prop_country|default:"-" }}</td>
        <td data-label="Status">
            {% if property.prop_title_deed %}
                <span class="status-uploaded">Available</span>
            {% else %}
                <span class="status-missing">Not Uploaded</span>
            {% endif %}
        </td>"""

CELLS_NOW = """        <td data-label="Property">{{ property.prop_name }}</td>
        <td data-label="Country">{{ property.prop_country|default:"-" }}</td>
        <td data-label="Status" class="text-center">
            {% if property.prop_title_deed %}
                <span class="alv-pill alv-pill-good">Available</span>
            {% else %}
                <span class="alv-pill alv-pill-neutral">Not Uploaded</span>
            {% endif %}
        </td>"""

ACTIONS_WAS = """                {% if property.prop_title_deed %}
                    <button type="button" class="btn btn-sm btn-danger" onclick="deleteDocument({{ property.prop_id }}, '{{ property.prop_name|escapejs }}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                {% else %}
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="uploadDocument({{ property.prop_id }}, '{{ property.prop_name|escapejs }}')">
                        <i class="fas fa-upload"></i> Upload
                    </button>
                {% endif %}"""

ACTIONS_NOW = """                {% if property.prop_title_deed %}
                    <span class="row-actions"><button type="button" class="icon-action-btn icon-delete" title="Delete title deed" aria-label="Delete title deed" onclick="deleteDocument({{ property.prop_id }}, '{{ property.prop_name|escapejs }}')">
                        <i class="fas fa-trash"></i>
                    </button></span>
                {% else %}
                    <span class="row-actions"><button type="button" class="icon-action-btn icon-upload" title="Upload title deed" aria-label="Upload title deed" onclick="uploadDocument({{ property.prop_id }}, '{{ property.prop_name|escapejs }}')">
                        <i class="fas fa-upload"></i>
                    </button></span>
                {% endif %}"""

BAR_WAS = """        <td class="mobile-action-bar">"""

BAR_NOW = """        <td class="mobile-action-bar cols-2">"""

# ------------------------------------------------------------- registers
SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------ NV-1b, 16 Oct 2026
    # Demetri: why does the Upload Title Deeds table not resemble our
    # standards. It wore no house class and re-declared base's whole
    # phone card block - fifteen rule openings, twelve of them base's.
    @{ File = 'pages\\templates\\title_deeds_management.html'; Text = 'class="table alv-table"'; What = 'the title deeds table wears the house table class' },
    @{ File = 'pages\\templates\\title_deeds_management.html'; Text = 'mobile-action-bar cols-2'; What = 'and asks base for the two columns it draws' },
    @{ File = 'pages\\templates\\title_deeds_management.html'; Text = '.mobile-action-bar'; Absent = $true; Code = $true; What = 'while declaring the bar NOWHERE itself - a page copy of that rule hid the bar on every phone' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

SUITE_WAS = """    'test_perm_select.py'
)"""

SUITE_NOW = """    'test_perm_select.py',
    'test_deed_table.py'
)"""

TREE_WAS = """    'test_perm_select.py',
]"""

TREE_NOW = """    'test_perm_select.py',
    # NV-1b, 16 Oct 2026 - the title deeds table onto .alv-table, and
    # fifteen rule openings out of the page's own stylesheet. Wide from
    # birth.
    'test_deed_table.py',
]"""

# THE PRINT ROUND'S QUEUE. test_print_leaks keeps a list of the pages
# that still hand-roll the card pattern and a list of what each
# migration left the queue FOR, so the check can say the queue SHRANK
# rather than merely that it changed. title_deeds_management leaves it
# here, and this round is what it left for.
PL_QUEUE_WAS = """    'title_deeds_management.html',
]"""

PL_QUEUE_NOW = """]"""

PL_MIG_WAS = """MIGRATED_P2 = ['projects/project_task_list.html']"""

PL_MIG_NOW = """MIGRATED_P2 = ['projects/project_task_list.html']
# Left the queue: 16 Oct 2026 round NV-1b (.bak_deedtable), after
# Demetri asked why the Upload Title Deeds table does not resemble our
# standards. It wore no house class at all and re-declared base's whole
# phone card block - fifteen rule openings, twelve of them base's. It
# wears .alv-table now, and its two Bootstrap buttons are
# icon-action-btns inside .row-actions.
MIGRATED_NV1B = ['title_deeds_management.html']"""

PL_OFF_WAS = """check('  and the eight migrated so far are off it',
      not (set(_cards) & (set(MIGRATED_H4) | set(MIGRATED_P2))),
      sorted(set(_cards) & (set(MIGRATED_H4) | set(MIGRATED_P2))))"""

PL_OFF_NOW = """check('  and the nine migrated so far are off it',
      not (set(_cards) & (set(MIGRATED_H4) | set(MIGRATED_P2)
                          | set(MIGRATED_NV1B))),
      sorted(set(_cards) & (set(MIGRATED_H4) | set(MIGRATED_P2)
                            | set(MIGRATED_NV1B))))"""

PL_CTRL_WAS = """      all(rel in TARGETS for rel in MIGRATED_H4 + MIGRATED_P2),
      [r for r in MIGRATED_H4 + MIGRATED_P2 if r not in TARGETS])"""

PL_CTRL_NOW = """      all(rel in TARGETS
          for rel in MIGRATED_H4 + MIGRATED_P2 + MIGRATED_NV1B),
      [r for r in MIGRATED_H4 + MIGRATED_P2 + MIGRATED_NV1B
       if r not in TARGETS])"""

ROUNDS_WAS = """    '.bak_permselect',
]"""

ROUNDS_NOW = """    '.bak_permselect',
    # NV-1b, 16 Oct 2026 - title_deeds_management's table takes
    # .alv-table and gives up its hand-rolled phone card block. The
    # status spans become alv-pills and the two Bootstrap buttons become
    # icon-action-btns inside .row-actions.
    '.bak_deedtable',
]"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('NV-1b REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def styles(t):
    """(start, end) of each <style> block's contents."""
    return [(m.start(1), m.end(1)) for m in
            re.finditer(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S)]


def find_rule(text, selector, lo, hi):
    """(start, end) of one rule, by selector, inside [lo, hi).

    Brace-matched, so the extracted anchor carries whatever whitespace
    the file really has - including the eight trailing spaces on a
    blank-looking line inside .mobile-action-bar, which is what an
    anchor typed by hand missed.
    """
    # THE SELECTOR GROUP SPANS LINES, AND THE FILE'S ENDINGS ARE THE
    # FILE'S. One entry here is a four-selector group written with \n,
    # and on a CRLF page an escaped \n matches nothing - the same class
    # of miss as an anchor typed without its real endings, which is what
    # fit() exists for everywhere else in this patcher.
    pat = re.compile(r'(?m)^[ \t]*'
                     + re.escape(selector).replace('\\\n', '\\r?\\n')
                     + r'\s*\{')
    out = []
    for m in pat.finditer(text, lo, hi):
        # A SELECTOR THAT CONTINUES A GROUP IS NOT A RULE. The
        # four-selector display:block group ends with the line
        # `.title-deeds-table td {`, which is also a rule of its own
        # fifteen lines later - so a line-anchored match found two and
        # refused a correct round. The test is what comes before it.
        k = m.start() - 1
        while k >= lo and text[k] in ' \t\r\n':
            k -= 1
        if k >= lo and text[k] == ',':
            continue
        i = m.end()
        depth, j = 1, i
        while depth and j < hi:
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
            j += 1
        if depth:
            refuse('%s: the rule for %s never closes' % (PAGE, selector))
        out.append((m.start(), j))
    return out


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED, asked of this round's own change to the TABLE TAG
    # rather than of any word a later round might also write.
    if re.search(r'<table[^>]*class="[^"]*\balv-table\b', read(page)):
        print('NV-1b  already applied - the table wears .alv-table.')
        return 0

    out = {}
    src = read(page)

    # ---------------------------------------------------------------- 1
    # base MUST own what is about to be deleted. Asserted against
    # base.html, not assumed, because twelve rules are coming out.
    base = read(alv_tree.path_of('base.html'))
    bcode = code_only(base)
    for need in ('.alv-table thead', 'attr(data-label)',
                 '.alv-table tbody td:first-child',
                 '.mobile-action-bar.cols-2',
                 '.alv-table thead th.col-center',
                 '.alv-pill-good', '.alv-pill-neutral',
                 '.icon-upload', '.icon-delete'):
        if need not in bcode:
            refuse('base does not declare %s, and this round hands it '
                   'twelve rules on that assumption' % need)
    # AND base NEUTRALISES the two Bootstrap table classes, which is why
    # dropping them changes nothing.
    if not re.search(r'\.alv-table\.table-bordered\s*\{[^}]*border:\s*0',
                     bcode):
        refuse('base no longer flattens .table-bordered on .alv-table, '
               'so dropping that class would move a border')
    if not re.search(r'\.alv-table\.table-striped[^{]*\{[^}]*transparent',
                     bcode):
        refuse('base no longer neutralises .table-striped on .alv-table, '
               'so dropping that class would move a stripe')

    # ---------------------------------------------------------------- 2
    # THE FIFTEEN, CUT BY SELECTOR WITH BRACE MATCHING.
    blocks = styles(src)
    if not blocks:
        refuse('%s has no <style> block' % PAGE)
    lo, hi = blocks[0][0], blocks[-1][1]

    # the phone block's bounds, so a selector cannot be cut from the
    # desktop half by accident
    mm = re.search(r'@media screen and \(max-width: 768px\)\s*\{', src)
    if not mm:
        refuse('%s: the phone query is not where this round measured it'
               % PAGE)
    p_lo = mm.end()
    depth, j = 1, p_lo
    while depth and j < len(src):
        if src[j] == '{':
            depth += 1
        elif src[j] == '}':
            depth -= 1
        j += 1
    p_hi = j - 1

    cuts = []
    for sel in PHONE_OUT:
        got = find_rule(src, sel, p_lo, p_hi)
        if len(got) != 1:
            refuse('%s: %r appears %d time(s) in the phone block, '
                   'expected 1' % (PAGE, sel, len(got)))
        cuts.append(got[0])
    for sel in TOP_OUT:
        got = [g for g in find_rule(src, sel, lo, hi)
               if not (p_lo <= g[0] < p_hi)]
        if len(got) != 1:
            refuse('%s: %r appears %d time(s) outside the phone block, '
                   'expected 1' % (PAGE, sel, len(got)))
        cuts.append(got[0])

    if len(cuts) != N_RULES_OUT:
        refuse('%s: %d rule(s) to cut, expected %d'
               % (PAGE, len(cuts), N_RULES_OUT))
    # non-overlapping, and the four-selector group is one cut
    cuts.sort()
    for a, b in zip(cuts, cuts[1:]):
        if a[1] > b[0]:
            refuse('%s: two cuts overlap - %r and %r' % (PAGE, a, b))

    s = src
    for a, b in reversed(cuts):
        s = s[:a] + s[b:]

    # the note goes where the first cut was
    s = s[:cuts[0][0]] + fit(src, NOTE) + '\n' + s[cuts[0][0]:]

    # ---------------------------------------------------------------- 3
    s = swap(s, TABLE_WAS, TABLE_NOW, '%s (the table tag and heads)' % PAGE)
    s = swap(s, CELLS_WAS, CELLS_NOW, '%s (the first three cells)' % PAGE)
    s = swap(s, ACTIONS_WAS, ACTIONS_NOW, '%s (the actions cell)' % PAGE)
    s = swap(s, BAR_WAS, BAR_NOW, '%s (the phone bar)' % PAGE)
    out[page] = s

    # ---------------------------------------------------------------- 4
    # GATES. EVERY ONE READS THE CODE, and the two that are about the
    # table tag read the TAG - not the page. A gate that searched the
    # whole page for table-striped found it in this round's own comment,
    # which is the fourth time that has happened this week.
    body = code_only(s)
    tag = re.search(r'<table[^>]*>', body)
    if not tag:
        refuse('%s: no table tag survives' % PAGE)
    cls = re.search(r'class="([^"]*)"', tag.group(0))
    cls = cls.group(1).split() if cls else []
    if sorted(cls) != ['alv-table', 'table']:
        refuse('%s: the table tag carries %r, expected table and '
               'alv-table' % (PAGE, cls))

    # THE PAGE DECLARES THE BAR NOWHERE. This is the gate that exists
    # because the first cut of this round hid the bar on every phone.
    stray = re.search(r'(?m)^[ \t]*\.mobile-action-bar[^{]*\{', body)
    if stray:
        refuse('%s: the page still declares %r. Its top-level copy loads '
               'after base and beats base phone display:grid on source '
               'order, which hides the action bar on every phone.'
               % (PAGE, stray.group(0).strip()))
    if DEAD_CLASS in body:
        refuse('%s: %s survives in the code, and every rule that named '
               'it has just been deleted' % (PAGE, DEAD_CLASS))
    for gone in ('status-uploaded', 'status-missing', 'btn-danger',
                 'btn-outline-primary'):
        if gone in body:
            refuse('%s: %s survives in the code' % (PAGE, gone))

    # the labels are still on the cells base reads them from
    n_lab = len(re.findall(r'<td\b[^>]*data-label="', body))
    if n_lab != 5:
        refuse('%s: %d cell(s) carry data-label, expected 5'
               % (PAGE, n_lab))
    if body.count('class="mobile-action-bar cols-2"') != 1:
        refuse('%s: the phone bar does not ask for two columns once'
               % PAGE)
    n_ra = len(re.findall(r'class="row-actions"', body))
    if n_ra != 3:
        refuse('%s: %d row-action strip(s), expected 3 - View, Delete '
               'and Upload' % (PAGE, n_ra))
    for pill in ('alv-pill alv-pill-good', 'alv-pill alv-pill-neutral'):
        if body.count(pill) != 1:
            refuse('%s: %s appears %d time(s), expected 1'
                   % (PAGE, pill, body.count(pill)))
    # AND THE ORDER IS THE VOCABULARY'S. upload is ADVANCE, delete is
    # DESTROY, and the markup is not told that - alv_rowactions is.
    try:
        import alv_rowactions as RA
        if not RA.FAMILY['upload'] < RA.FAMILY['delete']:
            refuse('alv_rowactions no longer sorts upload before delete, '
                   'and this round put them in that order on its word')
    except ImportError:
        refuse('alv_rowactions is not importable, and the order of the '
               'actions cell rests on it')

    # ---------------------------------------------------------------- 5
    p = os.path.join(root, PS1)
    s = read(p)
    if ME in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'NV-1b, 16 Oct 2026 - this round own suite. The title '
                  'deeds table takes .alv-table and gives up fifteen '
                  'rule openings, after Demetri asked why it does not '
                  'resemble our standards.',
                  '%s (the converted count)' % WD)

    # THE MARKUP CENSUS. Three of the four NV rounds move this counter,
    # so each bumps ITS OWN SHARE and matches the value its predecessor
    # left: NV-1b +2 here, NV-1c +1, NV-1d +1. A single round claiming
    # all four would be a number nobody measured per page.
    p = os.path.join(root, BH)
    out[p] = bump(read(p), 'N_BAR, N_ROW, N_MODAL = 267, %d, 95',
                  ROW_WAS_N, ROW_NOW_N,
                  'NV-1b, 16 Oct 2026 - the title deeds Actions cell drew '
                  'two Bootstrap buttons, which this census cannot see. '
                  'They are icon-delete and icon-upload now, so two '
                  'controls join the table-row count without a control '
                  'being added.',
                  '%s (the bar census)' % BH)

    # THE PRINT ROUND'S QUEUE, which this page has just left.
    p = os.path.join(root, PL)
    t = read(p)
    if 'MIGRATED_NV1B' in t:
        refuse('%s already records this migration' % PL)
    t = swap(t, PL_QUEUE_WAS, PL_QUEUE_NOW, '%s (the queue)' % PL)
    t = swap(t, PL_MIG_WAS, PL_MIG_NOW, '%s (what it left for)' % PL)
    t = swap(t, PL_OFF_WAS, PL_OFF_NOW, '%s (the migrated check)' % PL)
    t = swap(t, PL_CTRL_WAS, PL_CTRL_NOW, '%s (the control)' % PL)
    out[p] = t

    p = os.path.join(root, IB)
    out[p] = bump(read(p), 'IMP_TREE = %d', IMP_WAS, IMP_NOW,
                  'NV-1b, 16 Oct 2026 - thirteen of them went with the '
                  'title deeds phone card block. Every one was a copy of '
                  'a declaration base already makes, with the same '
                  '!important, so nothing changed about what wins - '
                  'there is simply one copy of each now. The page goes '
                  'from 14 to 1.',
                  '%s (the tree census)' % IB)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'NV-1b, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('NV-1b --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        print('   %d rule opening(s) would be cut' % len(cuts))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('NV-1b applied.')
    print('   the table wears table alv-table, and three columns ask')
    print('         for centring by name instead of the table asking')
    print('   %d rule opening(s) out of the page stylesheet - twelve'
          % len(cuts))
    print('         of them base owns, three of them top level')
    print('   the bar asks base for cols-2, and the page declares')
    print('         .mobile-action-bar NOWHERE - gated, because the')
    print('         first cut of this round hid it on every phone')
    print('   Available and Not Uploaded are alv-pills, good and')
    print('         NEUTRAL: no title deed yet is a state, not a fault')
    print('   Delete and Upload are icon-action-btns in .row-actions')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
