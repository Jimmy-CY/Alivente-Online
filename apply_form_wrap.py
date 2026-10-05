"""RA-3b - THE TEN BUTTONS THAT EACH LIVE IN THEIR OWN FORM.

   RA-3 wrapped 21 icon buttons on eight pages and held four pages back.
   Three of those four were held back for the same reason: their actions
   are not bare buttons but FORMS, one per action, because each posts
   somewhere different.

       household_member_management.html   3   edit, toggle-active, delete
       physical_invoice_list.html         6   approve, unapprove, send,
                                              duplicate, delete, and a PDF link
       invoices.html                      1   mark as paid

   A RUN OF BUTTONS WAS THE WRONG UNIT HERE. RA-3 grouped buttons with
   nothing but whitespace and template tags between them; between these
   there is a </form> and a <form>. Wrapping the buttons would have put a
   .row-actions INSIDE each form and left the forms themselves as
   siblings - three groups of one, which reads to the drift report as
   three action columns and tells it nothing about the order.

   SO THE UNIT IS THE CELL. Every one of the three pages puts its whole
   action column in a single <td>, and in each case the cell holds
   nothing but the actions. The wrapper goes immediately inside the <td>,
   around everything in it - forms, buttons, the {% if %} branches that
   choose between them, and the disabled <span> that stands in when a
   permission is missing.

   That is also why this could not be folded into RA-3: same destination,
   different rule, and a patcher that silently switched between two rules
   depending on what it found would be a patcher nobody could check.

   ONE CELL PER PAGE, measured before this was written. If a page ever
   grows a second action column the anchor stops matching exactly once
   and the round refuses rather than guessing which to take.

   FILES: three templates.                        [test_form_wrap.py]
"""
import os
import re
import sys

import alv_tree as T
import alv_rowactions as RA

SUFFIX = '.bak_formwrap'

OPEN_TAG = '<span class="row-actions">'
CLOSE_TAG = '</span>'

# page -> (the action cell's opening tag, how many loose buttons it holds)
CELLS = {
    'invoices.html': (
        '<td data-label="Actions" class="desktop-action-cell cell-actions">',
        1),
    'household_member_management.html': (
        '<td class=" hm-actions-cell cell-actions" data-label="Actions" '
        'style="white-space:nowrap;">',
        3),
    'physical_invoice_list.html': (
        '<td data-label="Actions" class="desktop-action-cell cell-actions '
        'pi-actions-cell">',
        6),
}

EXPECT_BUTTONS = 10


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


def page(name):
    hits = [p for p in T.templates()
            if T.rel(p).replace(os.sep, '/') == name]
    if len(hits) != 1:
        raise SystemExit('RA-3b: %s matched %d templates' % (name, len(hits)))
    return hits[0]


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    wrapped = 0
    buttons = 0
    for name, (tag, want) in sorted(CELLS.items()):
        path = page(name)
        text = read(path)

        n = text.count(tag)
        if n != 1:
            raise SystemExit(
                'RA-3b: the action cell on %s matched %d times, expected 1. '
                'If the page has grown a second action column, look at it '
                'rather than let the round pick one.' % (name, n))

        start = text.index(tag) + len(tag)
        # <td> CANNOT NEST, so the first </td> after it is the right one.
        end = text.find('</td>', start)
        if end < 0:
            raise SystemExit('RA-3b: the action cell on %s never closes' % name)

        inner = text[start:end]
        if 'row-actions' in inner:
            continue                     # already applied

        got = len(RA.BTN_FULL.findall(inner))
        if got != want:
            raise SystemExit('RA-3b: the %s cell holds %d icon control(s), '
                             'expected %d' % (name, got, want))

        # TEMPLATE BALANCE, as RA-3 checks: a wrapper around a block whose
        # {% if %} opens inside and closes outside crosses HTML nesting
        # with template nesting.
        if (len(re.findall(r'\{%\s*(?:if|for|with)\b', inner))
                != len(re.findall(r'\{%\s*end(?:if|for|with)\b', inner))):
            raise SystemExit('RA-3b: the %s cell is not template-balanced'
                             % name)

        text = text[:start] + OPEN_TAG + inner + CLOSE_TAG + text[end:]
        if not check:
            backup(path)
            write(path, text)
        wrapped += 1
        buttons += got

    print('RA-3b  cells wrapped   : %d' % wrapped)
    print('RA-3b  buttons grouped : %d' % buttons)

    if check:
        if wrapped:
            print('RA-3b  NOT APPLIED')
            return 1
        print('RA-3b  applied')
        return 0
    if wrapped not in (0, len(CELLS)) or buttons not in (0, EXPECT_BUTTONS):
        print('RA-3b  REFUSED: partial application (%d of %d cells, %d of %d '
              'buttons)' % (wrapped, len(CELLS), buttons, EXPECT_BUTTONS))
        return 2
    print('RA-3b  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
