"""TD-1 - THE WARNING BELONGS TO THE DATE, SO KEEP THEM ON ONE LINE.

   Demetri, 4 Oct 2026, on the Projects task list on a phone:

       "The Date, in Red, on a Task in the Task List on mobile, should fit
        the "!" on the right of the date, and not on the next line."

   THE MARKUP. The overdue cell is

       <span class="date-value overdue">
         01/02/2026
         <i class="fas fa-exclamation-triangle overdue-icon"></i>
       </span>

   The template puts the date and the icon on separate source lines, which
   is correct and readable, and leaves a text node of whitespace between
   them. A browser treats that whitespace as a space, and a space is a wrap
   opportunity. On a phone the table becomes cards, the value column is
   narrow, and the only wrap opportunity in the span is the one between the
   date and the warning - so that is where it breaks, and the triangle ends
   up alone under the date, pointing at nothing.

   THE FIX is `white-space: nowrap` on `.date-value`.

   WHY THAT IS SAFE AND NOT A GUESS. The span holds a date formatted
   d/m/Y - 01/02/2026, no spaces in it - and at most one icon. There is
   nothing in it that SHOULD wrap. The rendered width of the pair is 95px
   at 13px Courier, measured, against a card value column of 180px at 390.
   Nothing is pushed out of view; the suite renders it at 390, 360 and 320
   to say so rather than asserting it.

   WHY ON .date-value AND NOT ON THE ICON. `margin-left` on the icon is
   what SEPARATES the two; it is not what joins them. Joining them is a
   property of the line, and the line belongs to the span.

   .date-value is local to project_task_list.html - no other template in
   either tree uses the name - so this round touches one page and cannot
   reach anything else. A gate below proves that rather than trusting it.

   FILES: projects/project_task_list.html.    [test_overdue_date.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_overduedate'

PAGE = 'projects/project_task_list.html'

OLD = """.date-value {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: var(--alv-ink-soft);
}"""

NEW = """.date-value {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: var(--alv-ink-soft);
    /* TD-1, 4 Oct 2026. The overdue warning is written on its own source
       line after the date, which leaves a space between them, and a space
       is somewhere to wrap. On a phone card this column is the narrowest
       thing on the screen and that space was the only break in the span,
       so the triangle landed on the next line on its own. Demetri: the
       "!" "should fit ... on the right of the date, and not on the next
       line."

       A d/m/Y date has no spaces in it and the span holds nothing else,
       so there is nothing here that should wrap. Measured at 95px for the
       pair against a 180px card column at 390. */
    white-space: nowrap;
}"""


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def fit(text, block):
    """`block` written with the line ending `text` actually uses.

    106 of this tree's 142 templates are CRLF, and this one is. An anchor
    typed into a patcher is LF, so it matches zero times in a CRLF file -
    which is exactly what the first run of this round reported. Matching
    on a stripped copy and replacing in the real text would work too, but
    it loses the offsets; converting the anchor is the smaller lie."""
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    hits = [p for p in T.templates() if T.rel(p) == PAGE]
    if len(hits) != 1:
        raise SystemExit('TD-1: %s matched %d templates' % (PAGE, len(hits)))
    path = hits[0]

    # The name must stay local to this page, or a one-page round quietly
    # becomes a tree-wide one the next time someone copies the markup.
    users = [T.rel(p) for p in T.templates()
             if 'date-value' in read(p)]
    if users != [PAGE]:
        raise SystemExit('TD-1: .date-value is used by %s - this round was '
                         'written for one page' % users)

    text = read(path)
    old, new = fit(text, OLD), fit(text, NEW)
    if new in text:
        done = 0
    else:
        n = text.count(old)
        if n != 1:
            raise SystemExit('TD-1: the anchor appears %d times, expected 1'
                             % n)
        done = 1
        if not check:
            backup(path)
            write(path, text.replace(old, new))

    print('TD-1  edits applied : %d' % done)
    if check:
        if done:
            print('TD-1  NOT APPLIED')
            return 1
        print('TD-1  applied')
        return 0
    print('TD-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
