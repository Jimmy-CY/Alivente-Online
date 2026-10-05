"""RA-2 - WHAT THE DRIFT REPORT COULD NOT SEE.

   Show-RowActionDrift.py reads the tree through alv_rowactions.wrappers(),
   which finds <span> and <div> elements carrying .row-actions and looks at
   the buttons inside them. 83 icon buttons are inside one. THIRTY-SEVEN
   ARE NOT, across fourteen pages, and the report has never once mentioned
   them - not as a problem, not as a skip, not as a count.

   A report that is silent about a third of its subject is worse than no
   report, because it is believed. Three defects sat in that blind spot.

   1. .icon-view CARRYING FOUR PICTURES. fa-eye on eleven buttons, then
      fa-file-invoice on asset_detail, fa-file-pdf on
      physical_invoice_list and fa-scroll on title_deeds_management. RA-1
      created .icon-document and .icon-pdf for exactly this and repaired
      the ones it could see; these three it could not. It matters beyond
      tidiness because RA-1's ordering sorts on the NAME: a button called
      icon-view is placed as a LOOK at the record, and two of these are
      its papers, which WITHIN places after it.

   2. .icon-approve CARRYING fa-rotate-left on cash_receipts, where every
      other icon-approve is fa-check. Its own title says "Unvoid - bring
      back into use", which is an undo, and .icon-unapprove already exists
      and already draws fa-undo. The class said approve, the glyph said
      undo, the tooltip said unvoid.

   3. .icon-disabled USED AS A WHOLE NAME. On passport_management four
      buttons are classed `icon-action-btn icon-disabled` and nothing
      else, drawing fa-pencil-alt, fa-trash and fa-upload between them.
      One class, three pictures - but the real loss is that the markup no
      longer says what the action IS. A disabled Edit should be
      `icon-edit icon-disabled`: the name carries the verb, the modifier
      says it is unavailable. The report had excluded icon-disabled from
      its glyph census precisely BECAUSE it is a modifier, so this was
      invisible twice over.

   THE GLYPH CHANGES ARE DELIBERATE AND WERE CHOSEN. .icon-document
   already draws fa-file-contract on the Tenants lease agreement, so
   asset_detail's invoice and title_deeds' scroll take that glyph rather
   than the vocabulary growing two more classes. Demetri, 5 Oct 2026:
   "Reuse .icon-document, change the glyph (Recommended)".
   physical_invoice_list takes .icon-pdf, which already draws fa-file-pdf,
   so nothing changes on screen there at all - only the name, which is
   what the ordering reads.

   WHAT THIS ROUND DOES NOT DO. It does not wrap the 37. That turned out
   to be ~21 edits over fourteen pages - ten inside <td> elements where
   .row-actions' inline-flex would break the cell, three of those with
   {% elif %} branches and <form> elements interleaved - so it is a round
   of its own with its own renders. RA-2 makes the report NAME them.
   RA-3 can wrap them. Demetri: "Ship the report and the icon fixes now".

   FILES: five templates, alv_rowactions.py, Show-RowActionDrift.py.
                                                      [test_icon_names.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_iconnames'

# (page, old, new, what). Matched whole and exactly once each - a class
# rename done by loose substitution is how icon-view acquired its second
# picture in the first place.
EDITS = [
    # WHOLE BUTTONS, NOT TWO EDITS EACH. The first build changed the
    # class and the glyph as separate anchors, and fa-file-invoice
    # appears twice on asset_detail, fa-scroll three times on
    # title_deeds and fa-rotate-left twice on cash_receipts - so the
    # glyph edit would have hit whichever came first. The button is the
    # unit of this change, so the button is the anchor.
    ('asset_detail.html',
     '<button type="button" class="icon-action-btn icon-view" '
     'title="View invoice" onclick="viewInvoice(\'{{ record.invoice.url'
     '|escapejs }}\', \'{{ record.invoice.name|escapejs }}\')">\n'
     '                                    <i class="fas fa-file-invoice">'
     '</i>\n                                </button>',
     '<button type="button" class="icon-action-btn icon-document" '
     'title="View invoice" onclick="viewInvoice(\'{{ record.invoice.url'
     '|escapejs }}\', \'{{ record.invoice.name|escapejs }}\')">\n'
     '                                    <i class="fas fa-file-contract">'
     '</i>\n                                </button>',
     'the asset invoice button is a document, named and drawn as one'),

    ('title_deeds_management.html',
     '<button type="button" class="icon-action-btn icon-view" '
     'title="View title deed" aria-label="View title deed" '
     'onclick="viewDocument(\'{{ property.prop_title_deed.url|escapejs }}\', '
     '\'{{ property.prop_title_deed.name|escapejs }}\', '
     '\'{{ property.prop_name|escapejs }}\')">\n'
     '                    <i class="fas fa-scroll"></i>\n'
     '                </button>',
     '<button type="button" class="icon-action-btn icon-document" '
     'title="View title deed" aria-label="View title deed" '
     'onclick="viewDocument(\'{{ property.prop_title_deed.url|escapejs }}\', '
     '\'{{ property.prop_title_deed.name|escapejs }}\', '
     '\'{{ property.prop_name|escapejs }}\')">\n'
     '                    <i class="fas fa-file-contract"></i>\n'
     '                </button>',
     'and so is a title deed'),

    # Nothing visible changes here - .icon-pdf already draws fa-file-pdf.
    # Only the NAME was wrong, and the name is what the ordering sorts on.
    ('physical_invoice_list.html',
     'class="icon-action-btn icon-view" title="View invoice PDF"',
     'class="icon-action-btn icon-pdf" title="View invoice PDF"',
     'the invoice PDF button is named for what it is'),

    ('cash_receipts.html',
     '<button type="submit" class="icon-action-btn icon-approve" '
     'title="Unvoid \u2014 bring back into use">\n'
     '                      <i class="fas fa-rotate-left"></i>\n'
     '                    </button>',
     '<button type="submit" class="icon-action-btn icon-unapprove" '
     'title="Unvoid \u2014 bring back into use">\n'
     '                      <i class="fas fa-undo"></i>\n'
     '                    </button>',
     'unvoid is an unapprove, and takes the glyph that class draws'),

    # The modifier keeps its place; the verb comes back beside it. The
    # Edit/Delete pair is replaced together because this file holds two
    # identical disabled Edits and only this one is adjacent to a Delete -
    # replacing them one at a time would hit the wrong Edit first.
    ('passport_management.html',
     '<button type="button" class="icon-action-btn icon-disabled" disabled '
     'title="Edit"><i class="fas fa-pencil-alt"></i></button>\n'
     '                    <button type="button" class="icon-action-btn '
     'icon-disabled" disabled title="Delete"><i class="fas fa-trash">'
     '</i></button>',
     '<button type="button" class="icon-action-btn icon-edit icon-disabled" '
     'disabled title="Edit"><i class="fas fa-pencil-alt"></i></button>\n'
     '                    <button type="button" class="icon-action-btn '
     'icon-delete icon-disabled" disabled title="Delete"><i class="fas '
     'fa-trash"></i></button>',
     'a disabled Edit and Delete say which they are'),
    ('passport_management.html',
     '<button type="button" class="icon-action-btn icon-disabled" disabled '
     'title="Upload Document"><i class="fas fa-upload"></i></button>',
     '<button type="button" class="icon-action-btn icon-upload '
     'icon-disabled" disabled title="Upload Document"><i class="fas '
     'fa-upload"></i></button>',
     'and so does a disabled Upload'),
    ('passport_management.html',
     '<button type="button" class="icon-action-btn icon-disabled" disabled '
     'title="Edit"><i class="fas fa-pencil-alt"></i></button>',
     '<button type="button" class="icon-action-btn icon-edit icon-disabled" '
     'disabled title="Edit"><i class="fas fa-pencil-alt"></i></button>',
     'and the second disabled Edit'),
]


# ---- alv_rowactions learns to answer the other question -----------------

HELPER_OLD = "def blocks(inner):"

HELPER_NEW = '''# BTN_FULL, not BTN. alv_rowactions already defines a BTN further down -
# a single-group match on the class attribute alone - and a second
# module-level BTN simply shadows the first by source order, so
# unwrapped() called the OTHER one and m.group(2) raised IndexError on
# the first page it read. Two constants, two names.
BTN_FULL = re.compile(
    r\'<(?:button|a)[^>]*class="([^"]*\\bicon-action-btn\\b[^"]*)"[^>]*>\'
    r\'(.*?)</(?:button|a)>\', re.S)


def unwrapped(src):
    """[(classes, glyphs)] for every icon button NOT inside a wrapper.

    RA-2, 5 Oct 2026. wrappers() answers "what is inside a .row-actions",
    and every caller has treated that as "every icon button in the file".
    It is not: 37 of 120 are outside one. This is the other question,
    asked separately, so that no caller has to assume an answer it was
    never given.
    """
    spans = [(s, e) for s, e, _ in wrappers(src)]
    out = []
    for m in BTN_FULL.finditer(src):
        if any(s <= m.start() < e for s, e in spans):
            continue
        # FOUND BY PATTERN, NOT BY SPLITTING ON SPACES. A class attribute
        # in this tree is not a list of words - household_member writes
        #     class="icon-action-btn {% if m.is_active %}icon-lock
        #            {% else %}icon-unlock{% endif %}"
        # and splitting that yields the Django tags, no icon- token, and
        # a report that says the button has no icon class when it has
        # one of two chosen at render. The first build of this helper did
        # exactly that and named a perfectly correct button as a defect.
        names = [c for c in re.findall(r\'\\bicon-[\\w-]+\', m.group(1))
                 if c != \'icon-action-btn\']
        glyphs = [g for g in re.findall(r\'fa-[a-z-]+\', m.group(2))
                  if g not in (\'fa-fw\', \'fa-sm\', \'fa-lg\')]
        out.append((tuple(names), tuple(glyphs)))
    return out


def blocks(inner):'''


# ---- and the report learns to use it ------------------------------------

DECLARE_OLD = "rows = []\nglyphs = {}"

DECLARE_NEW = '''rows = []
glyphs = {}
# RA-2, 5 Oct 2026 - what is NOT in a wrapper.
#
# This report has always read the tree through RA.wrappers(), which finds
# .row-actions on a <span> or a <div>. 83 icon buttons are inside one;
# THIRTY-SEVEN ARE NOT, across fourteen pages, and the report said nothing
# about them at all.
#
# A report silent about a third of its subject is worse than no report,
# because it is believed. Inside this blind spot .icon-view carried four
# pictures, .icon-approve drew an undo arrow, and four passport buttons
# had no verb in their markup.
#
# They are NAMED here rather than failed on: wrapping all 37 is ~21 edits
# over fourteen pages, ten inside <td> elements where .row-actions\'
# inline-flex would break the cell. That is RA-3.
loose = {}'''

COLLECT_OLD = "    for s, e, inner in RA.wrappers(src):"

COLLECT_NEW = '''    for names, gl in RA.unwrapped(src):
        loose.setdefault(name, []).append((names, gl))
        # AND THE GLYPH CENSUS COUNTS THEM NOW. This is exactly where
        # .icon-view hid four pictures: the census only ever looked
        # inside wrappers, so three strays were never compared against
        # the eleven that were right.
        for c in names:
            if c != \'icon-disabled\' and gl:
                glyphs.setdefault(c, set()).add(gl[0])

    for s, e, inner in RA.wrappers(src):'''

PRINT_OLD = "line('=' * 74)\nif problems:"

PRINT_NEW = '''# NOT COUNTED AS DRIFT - named so the blind spot is visible, not so the
# report fails on work nobody has agreed to do. RA-3 wraps them.
if loose:
    n = sum(len(v) for v in loose.values())
    line(\'   NOT IN A .row-actions WRAPPER - %d button(s) on %d page(s).\'
         % (n, len(loose)))
    line(\'   The ordering standard cannot be read on these. Until RA-2\')
    line(\'   the glyph census could not see them either.\')
    for pg in sorted(loose):
        seen = sorted({\' \'.join(c) or \'(no icon class)\'
                       for c, _ in loose[pg]})
        line(\'     %-40s %2d  %s\' % (pg, len(loose[pg]), \', \'.join(seen)))
    line()

line(\'=\' * 74)
if problems:'''

TOOLING = [
    ('alv_rowactions.py', HELPER_OLD, HELPER_NEW),
    ('Show-RowActionDrift.py', DECLARE_OLD, DECLARE_NEW),
    ('Show-RowActionDrift.py', COLLECT_OLD, COLLECT_NEW),
    ('Show-RowActionDrift.py', PRINT_OLD, PRINT_NEW),
]


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    """The block written with the line ending the file really uses."""
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def page(name):
    hits = [p for p in T.templates() if T.rel(p) == name]
    if len(hits) != 1:
        raise SystemExit('RA-2: %s matched %d templates' % (name, len(hits)))
    return hits[0]


def edit_templates(check):
    done = 0
    by_page = {}
    for name, old, new, what in EDITS:
        by_page.setdefault(name, []).append((old, new, what))
    for name, items in sorted(by_page.items()):
        path = page(name)
        text = read(path)
        touched = 0
        for old, new, what in items:
            o, n = fit(text, old), fit(text, new)
            if n in text and o not in text:
                continue
            c = text.count(o)
            if c != 1:
                raise SystemExit('RA-2: on %s, %r matched %d times, '
                                 'expected 1' % (name, what, c))
            text = text.replace(o, n, 1)
            touched += 1
        if touched and not check:
            backup(path)
            write(path, text)
        done += touched
    return done


def edit_tooling(check):
    """Four edits over two files, applied to one in-memory copy each, so a
    second edit anchors against the first one's result rather than against
    the file on disk."""
    done = 0
    pending = {}
    for fname, old, new in TOOLING:
        text = pending.get(fname)
        if text is None:
            text = read(fname)
        o, n = fit(text, old), fit(text, new)
        if n in text:
            pending[fname] = text
            continue
        c = text.count(o)
        if c != 1:
            raise SystemExit('RA-2: %s anchor %r matched %d times, '
                             'expected 1'
                             % (fname, old.splitlines()[0], c))
        pending[fname] = text.replace(o, n, 1)
        done += 1
    if done and not check:
        for fname, text in pending.items():
            if text != read(fname):
                backup(fname)
                write(fname, text)
    return done


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    tmpl = edit_templates(check)
    tool = edit_tooling(check)

    print('RA-2  icon names corrected : %d' % tmpl)
    print('RA-2  tooling widened      : %d' % tool)

    if check:
        if tmpl or tool:
            print('RA-2  NOT APPLIED')
            return 1
        print('RA-2  applied')
        return 0
    if tmpl not in (0, len(EDITS)) or tool not in (0, len(TOOLING)):
        print('RA-2  REFUSED: partial application (%d/%d, %d/%d)'
              % (tmpl, len(EDITS), tool, len(TOOLING)))
        return 2
    print('RA-2  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
