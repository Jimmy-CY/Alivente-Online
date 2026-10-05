"""RA-3 - TWENTY-FOUR ICON BUTTONS GET THE WRAPPER THE STANDARD IS READ FROM.

   RA-2 widened the drift report and found that 37 of the tree's 119 icon
   buttons - a third - sat outside any .row-actions wrapper. The glyph
   census could reach them once it was widened; the ORDERING standard
   still cannot, because order is a property of a group and there was no
   group. This round makes the groups.

   SPLIT BY PAGE, NOT BY SHAPE, which is a correction to how I first
   proposed it. I had RA-3a/b/c/d carved up by what each button sits in -
   plain container, <td>, <form>, JavaScript. But three pages MIX those
   shapes, and converting by shape would have left those pages half
   wrapped: a .row-actions holding one action while two of its siblings
   stood outside it. That is worse than leaving the page alone, because
   the drift report would then read the group as complete and check the
   order of a fragment.

   So: nine pages where EVERY loose button is plain markup, all of them,
   now. The three mixed pages go to RA-3b with their forms, and
   create_meal_plan.html - whose three buttons are built inside a
   JavaScript template literal - to RA-3c.

       asset_detail.html                     2 runs,  3 buttons
       categories_management.html            2 runs,  4 buttons
       crs/fi_form.html                      2 runs,  2 buttons
       customer_invoice_form.html            2 runs,  2 buttons
       ingredient_base_units_management.html 2 runs,  4 buttons
       measurement_units_management.html     2 runs,  4 buttons
       physical_invoice_edit.html            2 runs,  2 buttons
       title_deeds_management.html           1 run,   1 button
       unit_conversions_management.html      1 run,   2 buttons
                                            16 runs, 24 buttons

   WHAT IT COSTS, MEASURED RATHER THAN FEARED. I warned Demetri that
   .row-actions being `inline-flex` would change the table cells. Painted:

       bare siblings (today)   cell 533x57   group span 111px
       .row-actions wrapper    cell 540x57   group span 114px
       at 390px                everything 0x0 - the cell is display:none

   Three pixels on the group, seven on the cell, at desktop; nothing at
   all on a phone, where the house card pattern hides the action cells.
   The three pixels are whitespace between inline buttons (about 4.5px)
   becoming base's `gap: 6px`. <span> and <div> measure identically.

   A RUN, NOT A BUTTON. Buttons are wrapped in GROUPS: a run is a set of
   loose buttons with nothing but whitespace and template tags between
   them. Two pages carry two runs in the same cell - the view-mode pair
   and the edit-mode pair - and those are two groups, not one, so they
   get a wrapper each. Every run was checked for template-tag balance
   before this was written: wrapping a run whose {% if %} opens inside it
   and closes outside would cross HTML nesting with template nesting.
   Sixteen runs, sixteen balanced.

   FILES: nine templates.                            [test_row_wrap.py]
"""
import os
import re
import sys

import alv_tree as T
import alv_rowactions as RA

SUFFIX = '.bak_rowwrap'

OPEN_TAG = '<span class="row-actions">'
CLOSE_TAG = '</span>'

# page -> (runs, buttons), measured before a line of this was written. An
# exact pair, not a floor: if a page has gained or lost a button since,
# this round should stop and be looked at rather than guess.
EXPECT = {
    # asset_detail.html IS NOT HERE, AND THAT IS THE ROUND'S BEST FINDING.
    # It was: 2 runs, 3 buttons. Wrapping them put a .row-actions inside a
    # .row-actions, which test_detail_property caught by counting
    # `.row-actions > *` and getting five where it wanted three.
    #
    # THE PAGE ALREADY HAD A WRAPPER. Two typos hid it: a <span> closed
    # with </button>, and the .row-actions <span> on line 250 never closed
    # at all - its <td> ends without one. The file holds 46 <span> and 44
    # </span>.
    #
    # alv_rowactions.wrappers() balances on its own tag name, so an
    # unbalanced file defeats it completely: it returned ZERO wrappers for
    # this page. The drift report has been calling three already-wrapped
    # buttons loose since the day the typo was made, and RA-2's census of
    # 37 was really 34. The fix is the two tags, not a wrapper.
    'categories_management.html': (2, 4),
    'crs/fi_form.html': (2, 2),
    'customer_invoice_form.html': (2, 2),
    'ingredient_base_units_management.html': (2, 4),
    'measurement_units_management.html': (2, 4),
    'physical_invoice_edit.html': (2, 2),
    'title_deeds_management.html': (1, 1),
    'unit_conversions_management.html': (1, 2),
}

# Whitespace and template tags only. Anything else between two buttons
# means they are not one group - a label, a form, another control.
GLUE = re.compile(r'^\s*(?:\{%[^%]*%\}\s*)*$')

OPENS = re.compile(r'\{%\s*(?:if|for|with|block)\b')
CLOSES = re.compile(r'\{%\s*end(?:if|for|with|block)\b')


# ------------------------------------------------- the squashed button
#
# THE WRAPPER DID NOT BREAK crs/fi_form.html. It revealed that the page's
# delete button had been drawing at 15.5px - under half its size - for as
# long as the row has been a grid.
#
# .in-row is `grid-template-columns: 1.2fr 2fr 110px 40px`, and the bare
# button, as a flex item of a 40px cell, was being shrunk to fit it. Put
# in a wrapper it stops shrinking and takes its proper 34px, which is 1px
# more than the page has to give. Painted:
#
#     before RA-3           button 15.5px   cell 40px   overflow  0
#     RA-3, column at 40px  button 34.0px   cell 40px   overflow +1
#     RA-3, column at 44px  button 34.0px   cell 44px   overflow  0
#
# So the column goes to 44px - which is also the house tap floor, C2's
# 'ALV TAP TARGET v1'. Demetri, shown the three measurements: "widen the
# column to 44px, inside RA-3".
#
# ONLY THE LAST VALUE. The 1.2fr, the 2fr and the 110px are the page's
# own layout and none of this round's business.
# The two tags that hid a wrapper from the tooling. Anchored on their
# own text, applied once each, both or neither.
ASSET = 'asset_detail.html'
TAGS = [
    ('<span class="icon-action-btn icon-disabled" title="No permission">\n                                    <i class="fas fa-trash"></i>\n                                </button>',
     '<span class="icon-action-btn icon-disabled" title="No permission">\n                                    <i class="fas fa-trash"></i>\n                                </span>'),
    ('                            {% endif %}\n                        </td>\n                    </tr>',
     '                            {% endif %}\n                          </span>\n                        </td>\n                    </tr>'),
]

FI_FORM = 'crs/fi_form.html'
GRID_OLD = 'grid-template-columns: 1.2fr 2fr 110px 40px;'
GRID_NEW = 'grid-template-columns: 1.2fr 2fr 110px 44px;'


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
    """CRLF if the file is CRLF. 106 of the 142 templates are, and an
    anchor written with bare newlines matches nothing in them."""
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def page(name):
    hits = [p for p in T.templates()
            if T.rel(p).replace(os.sep, '/') == name]
    if len(hits) != 1:
        raise SystemExit('RA-3: %s matched %d templates' % (name, len(hits)))
    return hits[0]


def loose(src):
    """Icon buttons in MARKUP that belong to no .row-actions wrapper.

    Script is excluded deliberately: create_meal_plan.html builds three
    of these inside a JavaScript template literal, and editing markup
    inside a JS string is its own risk class and its own round."""
    wraps = [(a, b) for a, b, _ in RA.wrappers(src)]
    scripts = [(m.start(1), m.end(1)) for m in
               re.finditer(r'<script[^>]*>(.*?)</script>', src, re.S | re.I)]
    out = []
    for m in RA.BTN_FULL.finditer(src):
        if any(a <= m.start() < b for a, b in wraps):
            continue
        if any(a <= m.start() < b for a, b in scripts):
            continue
        out.append((m.start(), m.end()))
    return out


def runs_of(src):
    """Loose buttons grouped into the sets that share a row."""
    runs = []
    for b in loose(src):
        if runs and GLUE.match(src[runs[-1][-1][1]:b[0]]):
            runs[-1].append(b)
        else:
            runs.append([b])
    return runs


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    wrapped = 0
    touched = 0
    for name, (want_runs, want_btns) in sorted(EXPECT.items()):
        path = page(name)
        text = read(path)
        runs = runs_of(text)
        if not runs:
            continue                      # already applied

        got = (len(runs), sum(len(r) for r in runs))
        if got != (want_runs, want_btns):
            raise SystemExit(
                'RA-3: %s has %d run(s) of %d button(s), expected %d of %d. '
                'The page has changed since this round was measured; look at '
                'it rather than let the round guess.'
                % (name, got[0], got[1], want_runs, want_btns))

        # BALANCE, EVERY TIME, not just when it was surveyed. A run whose
        # {% if %} opens inside it and closes outside cannot be wrapped
        # without crossing HTML nesting with template nesting.
        for r in runs:
            seg = text[r[0][0]:r[-1][1]]
            if len(OPENS.findall(seg)) != len(CLOSES.findall(seg)):
                raise SystemExit('RA-3: a run on %s is not template-balanced'
                                 % name)

        # LAST TO FIRST, so the offsets of the runs still ahead stay true.
        for r in reversed(runs):
            a, z = r[0][0], r[-1][1]
            text = text[:a] + OPEN_TAG + text[a:z] + CLOSE_TAG + text[z:]
            wrapped += 1

        if not check:
            backup(path)
            write(path, text)
        touched += 1

    # --- the two tags that hid asset_detail's wrapper from the tooling
    tags = 0
    ap = page(ASSET)
    atext = read(ap)
    for old, new in TAGS:
        o, w = fit(atext, old), fit(atext, new)
        if w in atext and o not in atext:
            continue
        n = atext.count(o)
        if n != 1:
            raise SystemExit('RA-3: an asset_detail tag anchor matched %d '
                             'times, expected 1' % n)
        atext = atext.replace(o, w, 1)
        tags += 1
    if tags:
        if tags != len(TAGS):
            raise SystemExit('RA-3: asset_detail needs both tags or '
                             'neither (%d of %d)' % (tags, len(TAGS)))
        if not check:
            backup(ap)
            write(ap, atext)

    # --- and the column that was squeezing the button it now holds
    grid = 0
    fi = page(FI_FORM)
    fitext = read(fi)
    if GRID_NEW not in fitext:
        n = fitext.count(GRID_OLD)
        if n != 1:
            raise SystemExit('RA-3: the fi_form grid matched %d times' % n)
        fitext = fitext.replace(GRID_OLD, GRID_NEW, 1)
        if not check:
            backup(fi)
            write(fi, fitext)
        grid = 1

    print('RA-3  tags repaired : %d' % tags)
    print('RA-3  runs wrapped : %d' % wrapped)
    print('RA-3  pages        : %d' % touched)
    print('RA-3  grid widened : %d' % grid)

    if check:
        if wrapped or grid or tags:
            print('RA-3  NOT APPLIED')
            return 1
        print('RA-3  applied')
        return 0
    if wrapped not in (0, sum(v[0] for v in EXPECT.values())):
        print('RA-3  REFUSED: partial application (%d of %d runs)'
              % (wrapped, sum(v[0] for v in EXPECT.values())))
        return 2
    print('RA-3  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
