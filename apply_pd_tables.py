# -*- coding: utf-8 -*-
"""PD-2 - property_detail's SEVEN TABLES COME TO base

PD-1 took the palette. This takes the tables themselves, which is the
round that makes the page follow base from here on rather than being
repainted to match it every time base moves.

==========================================================================
THE PAGE HAD REBUILT base's PHONE CARD BY HAND
==========================================================================
Thirty-five rules in one @media block, and twenty-three of them are
declaration-for-declaration what base's .alv-table already does:

    .issues-table thead                     { display: none }
    .issues-table, ... tbody, tr, td        { display: block; width: 100% }
    .issues-table tbody tr                  { background: white; border:
                                              1px solid #dee2e6; radius 8px }
    .issues-table td::before                { content: attr(data-label) }
    .issues-table td[data-label="Issue"]    { 15px, 600, promoted }
    .issues-table td[data-label="Issue"]::before { display: none }

base says the same thing once, for every table in the app:

    .alv-table thead                        { display: none }
    .alv-table, tbody, tfoot, tr, td        { display: block; width: 100% }
    .alv-table tbody tr                     { background: var(--alv-paper) }
    .alv-table td::before                   { content: attr(data-label) }
    .alv-table tbody td:first-child         { 16px, 600, no label }

EVERY ONE OF THE SEVEN ALREADY CARRIES data-label ON EVERY CELL, so the
house card works the moment the class is on. That is the whole reason
this round is tractable: the markup was already shaped for it.

==========================================================================
ONE TABLE KEEPS ITS OWN TITLE RULE, AND IT IS NAMED
==========================================================================
base promotes the FIRST cell. On six of the seven that is already the
cell the page promotes by hand:

    assets-table    Asset Name          first
    issues-table    Issue               first
    expenses-table  Expense Line Type   first
    revenue-table   Revenue Line Type   first

actual-expenses-table is the exception. Its first cell is the DATE and
the page promotes the DESCRIPTION. Letting base take it would silently
change what that card leads with, so the local promotion stays and
base's first-child rule is suppressed for that one table. Written down
here rather than quietly resolved: if an expense card should lead with
its date like every other card leads with its first column, that is one
line to delete and Demetri's call, not mine.

==========================================================================
NO ZEBRA
==========================================================================
Demetri, asked: "Lose the stripes." Five of the seven wore Bootstrap's
table-striped. base's .alv-table has no zebra and a suite already
asserts it on another page - every list in this app draws its rows one
colour with a line between them. The classes go with the conversion.

==========================================================================
AND THE ONE ACTION ON ANY OF THESE TABLES
==========================================================================
Issues has a Comments button, 83x31 - under the 44px tap target.
Demetri, asked: "A row action icon." It becomes .icon-action-btn
.icon-comment inside a .row-actions cell, which puts it at 34px on a
desktop and 44 on a phone and in the column position RA-1 standardised.

.icon-comment is the SEVENTH NAME on --alv-view, by the rule base states
beside .icon-duplicate, .icon-manage, .icon-list and the three RA-1
added this morning: reading what somebody wrote about an issue is a
LOOK, so it takes that colour and its own name, because a class carries
one picture. Nothing is added to the palette.

Backups: .bak_pdtables. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_pdtables'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree
from alv_pd2_drop import DROP

PAGE = alv_tree.path_of('property_detail.html')
BASE = alv_tree.path_of('base.html')


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
            raise SystemExit('PD2: %s is not a byte copy' % bak)


def swap(nl, old, new, what, times=1):
    c = nl.count(old)
    if c != times:
        raise SystemExit('PD2: %s appears %d times, not %d' % (what, c, times))
    return nl.replace(old, new)


print('=' * 74)
print('PD-2 - property_detail: seven tables come to base%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. base GAINS .icon-comment.
# ==========================================================================
b, braw = read(BASE)
bnl = b.replace('\r\n', '\n')

ICON = """
      /* Comment: the SEVENTH NAME on --alv-view, added by PD-2 on 4 Oct
         2026 for the Property Issues row action (fa-comments). Reading
         what somebody wrote about an issue SHOWS you something and
         changes nothing, which is what this colour means here.

         Its own name, by the rule three blocks up: a class carries ONE
         PICTURE, so fa-comments does not go on .icon-view beside the
         eye. Alias the colour, never the name. Nothing is added to the
         palette.                            [test_pd_tables.py] */
      .icon-comment       { color: var(--alv-view); border-color: var(--alv-accent-line); }
      .icon-comment:hover { background: var(--alv-view); border-color: var(--alv-view); color: var(--alv-on-accent); }
      .icon-color-comment { color: var(--alv-view); }
"""

if 'PD-2 on 4 Oct' in bnl:
    print('  base.html                  already defines .icon-comment')
else:
    if '.icon-comment' in bnl:
        raise SystemExit('PD2: base.html already names .icon-comment')
    # BESIDE THE OTHER NAMES ON THIS COLOUR, and in the style block that
    # holds the tokens - RA-1 paid for putting three of them in a block
    # some probes do not load.
    anchor = ('      .icon-color-assets { color: var(--alv-view); }\n')
    bnl = swap(bnl, anchor, anchor + ICON, 'the icon-assets terminator')
    out = bnl.replace('\n', '\r\n') if CRLF.get(BASE) else bnl
    if not CHECK:
        back_up(BASE, braw)
        write(BASE, out)
    print('  base.html                  .icon-comment, a NAME on --alv-view')

# ==========================================================================
# 2. THE SEVEN TABLES TAKE THE CLASS.
# ==========================================================================
t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')

if 'PD-2, 4 Oct 2026' in nl:
    print('  property_detail.html       already on base\'s table')
    print('=' * 74)
    print('PD-2 applied')
    print('=' * 74)
    raise SystemExit(0)

# `table alv-table`, NOT `alv-table` alone. Bootstrap's .table is what
# sets width: 100%; base's .alv-table sets the house look and nothing
# about geometry. The first build of this round dropped .table with the
# striping and the seven tables shrank to fit their content - the Issues
# table ended at 555px in a 1145px panel, which the render showed and no
# text check would have. The tree agrees: 20 of the 24 .alv-table tags in
# this app are written `table alv-table`.
TABLES = [
    ('<table class="categories-table">',
     '<table class="table alv-table categories-table">'),
    ('<table class="assets-table">',
     '<table class="table alv-table assets-table">'),
    ('<table class="table table-striped table-hover actual-expenses-table">',
     '<table class="table alv-table actual-expenses-table">'),
    ('<table class="table table-striped table-hover issues-table">',
     '<table class="table alv-table issues-table">'),
    ('<table class="table table-striped table-hover expenses-table">',
     '<table class="table alv-table expenses-table">'),
    ('<table class="table table-striped table-hover revenue-table">',
     '<table class="table alv-table revenue-table">'),
    ('<table class="table table-striped table-hover invoices-table">',
     '<table class="table alv-table invoices-table">'),
]
for old, new in TABLES:
    nl = swap(nl, old, new, 'the %s tag' % old.split('"')[1].split()[-1])

# ==========================================================================
# 3. THE RULES base NOW PROVIDES.
# ==========================================================================
# TAKEN VERBATIM out of the file, in alv_pd2_drop.py, rather than retyped
# here - 23 rules of hand-built card machinery is 23 chances to mistype
# one and have the swap gate refuse for the wrong reason.
for i, rule in enumerate(DROP):
    nl = swap(nl, rule + '\n', '', 'phone rule %d (%s)'
              % (i, ' '.join(rule.split())[:46]))

DESK = [
    ('PD-1\'s consolidated header',
     re.compile(r'/\* PD-1, 4 Oct 2026 - FIVE RULES, ONE HEADER\..*?\n\}\n', re.S)),
    ('PD-1\'s row-coloured header',
     re.compile(r'/\* PD-1, 4 Oct 2026 - the other two dark headers\..*?\n\}\n'
                r'(?=\.categories-table th)', re.S)),
    ('the categories/assets th rule',
     re.compile(r'\.categories-table th,\n\.assets-table th \{[^}]*\}\n')),
    ('the categories/assets table rule',
     re.compile(r'\.categories-table,\n\.assets-table \{[^}]*\}\n')),
    ('the assets font-size',
     re.compile(r'\.assets-table \{ font-size: 0\.9rem; \}\n')),
    ('the categories/assets td rule',
     re.compile(r'\.categories-table td,\n\.assets-table td \{[^}]*\}\n')),
]
for what, rx in DESK:
    hits = rx.findall(nl)
    if len(hits) != 1:
        raise SystemExit('PD2: %s appears %d times, not once' % (what, len(hits)))
    nl = rx.sub('', nl, count=1)

NOTE = """/* PD-2, 4 Oct 2026 - THE TABLES ARE base's NOW.

   This page had rebuilt base's phone card by hand: 23 rules of
   `thead { display: none }`, block display, a white card with a
   #dee2e6 border and a radius, `td::before { content: attr(data-label) }`
   and a promoted first cell - declaration for declaration what
   .alv-table has said for every table in the app since it was written.
   Seven table headers in two different darks went with them, and so did
   Bootstrap's table-striped: Demetri, asked, "Lose the stripes."

   Every one of the seven already carried data-label on every cell, which
   is the only reason this was a class change rather than a rewrite.

   WHAT STAYS LOCAL, and why:
     - the Warranty Expiry cell is right-aligned
     - the Issues Description cell stacks its label above its text
     - the Comments cell keeps its divider
     - an OVERDUE invoice card keeps its red tint
     - the amount figures keep their size
     - and actual-expenses promotes its DESCRIPTION, because its first
       cell is the Date and base promotes the first cell. The suppression
       below is what keeps that card leading with what it led with
       before. If it should lead with the date like every other card
       leads with its first column, delete these two rules. */
.alv-table.actual-expenses-table tbody td:first-child {
    font-size: inherit;
    font-weight: inherit;
    padding-bottom: 6px !important;
    margin-bottom: 0;
    border-bottom: none;
}
.alv-table.actual-expenses-table tbody td:first-child::before {
    content: attr(data-label);
}
"""

# WRITTEN WHERE THE RULES IT EXPLAINS USED TO BE.
anchor = '.categories-table th.count-col { width: 150px; }\n'
nl = swap(nl, anchor, NOTE + anchor, 'the count-col anchor')

# ==========================================================================
# 4. THE COMMENTS BUTTON BECOMES A ROW ACTION.
# ==========================================================================
m = re.search(r'<td[^>]*data-label="Comments"[^>]*>.*?</td>', nl, re.S)
if not m:
    raise SystemExit('PD2: the Comments cell is not where this round left it')
cell = m.group(0)
link = re.search(r'<a\b[^>]*>.*?</a>', cell, re.S)
if not link:
    raise SystemExit('PD2: the Comments cell has no link in it')
href = re.search(r'href="([^"]*)"', link.group(0))
NEW_CELL = (
    '{# data-label KEPT, and not desktop-action-cell. Every other list #}\n'
    '                                                        '
    '{# in this app puts its actions in a .desktop-action-cell, which  #}\n'
    '                                                        '
    '{# base HIDES on a phone because a .mobile-action-bar carries     #}\n'
    '                                                        '
    '{# them there instead. This page has no such bar, so the cell     #}\n'
    '                                                        '
    '{# stays visible and keeps its label - an unlabelled lone icon in #}\n'
    '                                                        '
    '{# a card, with nothing else to explain it, is a worse card.      #}\n'
    '                                                        '
    '<td data-label="Comments" class="cell-actions">\n'
    '                                                            '
    '{# PD-2 - a ROW ACTION, not a labelled button. It measured 83x31, #}\n'
    '                                                            '
    '{# under the 44px tap target, and it is the only action on any of #}\n'
    '                                                            '
    '{# the seven tables here. Demetri, asked: "A row action icon."    #}\n'
    '                                                            '
    '<span class="row-actions">\n'
    '                                                              '
    '<a href="%s" class="icon-action-btn icon-comment" title="Comments">\n'
    '                                                                '
    '<i class="fas fa-comments"></i>\n'
    '                                                              </a>\n'
    '                                                            </span>\n'
    '                                                        </td>' % href.group(1))
nl = swap(nl, cell, NEW_CELL, 'the Comments cell')

out = nl.replace('\n', '\r\n') if CRLF.get(PAGE) else nl
if not CHECK:
    back_up(PAGE, raw)
    write(PAGE, out)
print('  property_detail.html       7 tables on .alv-table, 29 rules out')

print('=' * 74)
print('PD-2 %s' % ('would apply' if CHECK else 'applied'))
print('=' * 74)
