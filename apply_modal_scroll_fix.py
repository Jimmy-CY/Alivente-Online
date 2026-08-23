#!/usr/bin/env python3
"""
apply_modal_scroll_fix.py
=========================

The delete dialogs outgrew the screen.

What happened
-------------
The line-type delete modal already showed a scrolling list of every linked
expense, capped at 50vh. Adding the close-or-purge choice underneath pushed the
body past the viewport, and since nothing constrained the modal's height the
footer - Cancel and Delete - fell off the bottom. On a 768px-high screen with
ten linked expenses there was no way to reach the buttons.

Only the mobile breakpoint had ever handled this: it makes the modal
full-height with a scrolling body. Desktop had no equivalent.

The fix
-------
The standard flex pattern, applied to both delete dialogs:

    .modal-content   capped at the viewport, laid out as a column
    .modal-header    fixed
    .modal-body      the only part that scrolls (min-height:0 so a flex child
                     can actually shrink - without it the body refuses to
                     scroll and overflows anyway)
    .modal-footer    fixed, so the buttons are always reachable

The linked-expense list also drops from 50vh to 26vh. It has its own scrollbar,
so nothing is lost, and it stops one long list burying the choice below it.

Files touched
-------------
  pages/templates/finance_expense_line_types.html   #deleteModal
  pages/templates/finance_expense.html              #expenseDeleteModal

Idempotent; backs each file up on first run (.bak_modalfit).

    python apply_modal_scroll_fix.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
LT_FORM = os.path.join(TPL, 'finance_expense_line_types.html')
LIST_FORM = os.path.join(TPL, 'finance_expense.html')

SENTINEL = 'delete-dialog fits the viewport'


# --- shared rule text, one selector substituted ---------------------------

FIT_CSS = '''
/* Keep the %(what)s dialog inside the viewport so the buttons stay
   reachable. The body is the only part that scrolls; min-height:0 is what
   lets a flex child actually shrink instead of overflowing its parent.
   (delete-dialog fits the viewport) */
%(sel)s .modal-content {
    max-height: calc(100vh - 3.5rem);
    display: flex;
    flex-direction: column;
}
%(sel)s .modal-header,
%(sel)s .modal-footer {
    flex: 0 0 auto;
}
%(sel)s .modal-body {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
}
'''

LT_ANCHOR = '''#deleteModal .modal-footer {
    border-top: 1px solid #e9ecef;
    padding: 14px 22px;
}
'''

LT_LIST_OLD = '''.expense-detail-list {
    max-height: 50vh;
    overflow-y: auto;
'''

LT_LIST_NEW = '''.expense-detail-list {
    /* Was 50vh. With the delete choice underneath, half the screen of expense
       cards pushed everything else out of sight. It scrolls on its own. */
    max-height: 26vh;
    overflow-y: auto;
'''

LIST_ANCHOR = '''<!-- Delete: stop from a date, or remove the past as well. A native
     confirm() cannot ask this, and the answer changes what closed years say
     they cost. -->
'''

LIST_STYLE = '<style>%s</style>\n\n' % (FIT_CSS % {
    'what': 'expense delete', 'sel': '#expenseDeleteModal'})


def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_modalfit'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    for p in (LT_FORM, LIST_FORM):
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    lt_src, lt_enc, lt_nl = sniff(LT_FORM)
    list_src, list_enc, list_nl = sniff(LIST_FORM)

    if 'ltd-choice' not in lt_src or 'expenseDeleteModal' not in list_src:
        print('! apply_delete_choice.py has not been applied.')
        print('  Run that first - this fixes the dialogs it adds to.')
        return 1

    lt_done = SENTINEL in lt_src
    list_done = SENTINEL in list_src
    if lt_done and list_done:
        print('= already applied - nothing to do')
        return 0

    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if not lt_done:
        need('line-types modal footer rule', lt_src, LT_ANCHOR)
        need('line-types expense list rule', lt_src, LT_LIST_OLD)
    if not list_done:
        need('expenses list dialog comment', list_src, LIST_ANCHOR)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    if not lt_done:
        lt_src = lt_src.replace(
            LT_ANCHOR,
            LT_ANCHOR + (FIT_CSS % {'what': 'line-type delete',
                                    'sel': '#deleteModal'}), 1)
        lt_src = lt_src.replace(LT_LIST_OLD, LT_LIST_NEW, 1)

    if not list_done:
        list_src = list_src.replace(LIST_ANCHOR, LIST_STYLE + LIST_ANCHOR, 1)

    if CHECK:
        print('= check only: every anchor matched, nothing written')
        return 0

    if not lt_done:
        write_back(LT_FORM, lt_src, lt_enc, lt_nl)
        print('+ pages/templates/finance_expense_line_types.html   '
              'dialog fits, list capped at 26vh')
    if not list_done:
        write_back(LIST_FORM, list_src, list_enc, list_nl)
        print('+ pages/templates/finance_expense.html              dialog fits')

    print('')
    print('Backups: .bak_modalfit alongside each file.')
    print('Verify:  hard-refresh the page (Ctrl+F5) - this is CSS, so a cached')
    print('         stylesheet will look unchanged.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
