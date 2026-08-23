#!/usr/bin/env python3
"""
fix_prorata_comment.py
======================

A Django `{# ... #}` comment CANNOT span more than one line.

The comment I put above the greyed-out Delete control ran to two lines, so the
template parser never recognised it as a comment and rendered it as literal
text - which then wrapped inside the narrow Action column and blew the row's
height out to half a screen.

    {# A share of the line type's amount, not a standalone figure. Deleting
       one row would leave the others holding shares of a larger split. #}

Two ways to write a multi-line comment properly - `{% comment %}...{% endcomment %}`
or one `{# #}` per line. This just collapses it to a single line; the reasoning
lives in apply_prorata_delete_guard.py and in the view, which is where anyone
changing the behaviour will actually be looking.

The explanation the user needs is the `title` attribute on the span, which was
always there and shows on hover. Nothing else about the guard changes.

Idempotent; backs the file up on first run (.bak_prcomment).

    python fix_prorata_comment.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
FORM = os.path.join(ROOT, 'pages', 'templates', 'finance_expense.html')

BROKEN = """                                                    {# A share of the line type's amount, not a standalone figure. Deleting
                                                       one row would leave the others holding shares of a larger split. #}
"""

FIXED = """                                                    {# A share of the line type amount - deleting one row would leave the others holding shares of a larger split. #}
"""


def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def main():
    if not os.path.exists(FORM):
        print('! %s not found - run from the project root'
              % os.path.relpath(FORM, ROOT))
        return 1

    src, enc, nl = sniff(FORM)

    if BROKEN not in src:
        if FIXED.strip() in src:
            print('= already applied - nothing to do')
            return 0
        # Neither form present: the guard has not been applied, or the comment
        # was edited by hand. Say which rather than guessing.
        if 'btn-row-delete-disabled" title="Pro-rata' in src:
            print('= the two-line comment is not there - nothing to fix')
            return 0
        print('! apply_prorata_delete_guard.py has not been applied.')
        return 1

    n = src.count(BROKEN)
    if n != 1:
        print('! the broken comment matched %d times, expected 1' % n)
        print('  Aborting - nothing written.')
        return 1

    src = src.replace(BROKEN, FIXED, 1)

    # A stray {# with no closing #} on the same line would be rendered as text
    # again, which is the whole bug. Check every one before writing.
    for i, line in enumerate(src.split('\n'), 1):
        if '{#' in line and '#}' not in line:
            print('! line %d opens a {# comment that does not close on the '
                  'same line - Django would render it as text' % i)
            print('  Aborting - nothing written.')
            return 1

    if CHECK:
        print('= check only: the two-line comment was found and every {# #} '
              'closes on its own line, nothing written')
        return 0

    bak = FORM + '.bak_prcomment'
    if not os.path.exists(bak):
        shutil.copy2(FORM, bak)
    with open(FORM, 'w', encoding=enc, newline='') as fh:
        fh.write(src.replace('\n', nl) if nl == '\r\n' else src)

    print('+ pages/templates/finance_expense.html   comment collapsed to one line')
    print('')
    print('Backup: .bak_prcomment. Refresh the Expenses list - the Action')
    print('column should be back to Edit and a greyed-out Delete, with the')
    print('explanation on hover.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
