#!/usr/bin/env python3
"""
fix_disabled_tooltip.py
=======================

A disabled control that cannot explain why it is disabled.

Both greyed-out controls in the Expenses list carry a `title` - "No permission
to delete", and now "Pro-rata expense - remove this property by editing the
line...". Neither has ever appeared on hover, because both classes set:

    pointer-events: none;

That does exactly what it says: the element receives no pointer events at all,
so the browser never registers a hover and never shows the tooltip. The
explanation was there the whole time and unreachable.

It was presumably added to stop clicks. It is not needed for that - neither
element is a link, a button or a form control, and neither has a click handler.
`cursor: not-allowed` is what makes it read as disabled, and that still works.

So pointer events go back on for both variants. The pro-rata tooltip starts
working, and so does the permission one, which has been silently broken for as
long as it has existed.

Note the native tooltip has the usual ~1 second delay before it appears - that
is the browser, not the page. If it wants to be instant and styled, that is a
CSS ::after tooltip, which is a bigger change inside a table cell and worth
doing deliberately rather than as part of a fix.

Files touched
-------------
  pages/templates/finance_expense.html   one CSS rule appended

Idempotent; backs the file up on first run (.bak_tooltip).

    python fix_disabled_tooltip.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
FORM = os.path.join(ROOT, 'pages', 'templates', 'finance_expense.html')

SENTINEL = 'hover-explains-disabled'

ANCHOR = """.btn-row-delete-disabled {
    background: #f8f9fa;
    color: #adb5bd;
    border: 2px solid #dee2e6;
    padding: 5px 14px;
    border-radius: 6px;
    font-size: 13px;
    cursor: not-allowed;
    pointer-events: none;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
"""

ADD = """
/* hover-explains-disabled
   Both disabled variants above set pointer-events:none, which suppresses hover
   entirely - so their `title` never appeared, and a disabled control still has
   to be able to say why it is disabled. Restored here rather than edited above,
   so the reason is recorded next to the fix.

   Nothing becomes clickable: these are spans, not links or buttons, and
   neither carries a click handler. cursor:not-allowed still reads as disabled. */
.btn-row-edit-disabled,
.btn-row-delete-disabled {
    pointer-events: auto;
}
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

    if SENTINEL in src:
        print('= already applied - nothing to do')
        return 0

    n = src.count(ANCHOR)
    if n != 1:
        print('! .btn-row-delete-disabled rule matched %d times, expected 1' % n)
        print('  Aborting - nothing written.')
        return 1

    src = src.replace(ANCHOR, ANCHOR + ADD, 1)

    # The override has to come AFTER both rules it is undoing, or equal
    # specificity loses and nothing changes.
    if src.index(SENTINEL) < src.rindex('pointer-events: none;'):
        print('! the override lands before a pointer-events:none it must beat')
        print('  Aborting - nothing written.')
        return 1

    if CHECK:
        print('= check only: the rule was found and the override lands after '
              'it, nothing written')
        return 0

    bak = FORM + '.bak_tooltip'
    if not os.path.exists(bak):
        shutil.copy2(FORM, bak)
    with open(FORM, 'w', encoding=enc, newline='') as fh:
        fh.write(src.replace('\n', nl) if nl == '\r\n' else src)

    print('+ pages/templates/finance_expense.html   disabled controls accept hover')
    print('')
    print('Backup: .bak_tooltip. This is CSS - hard-refresh (Ctrl+F5).')
    print('Hover a greyed-out Delete and hold for about a second; the native')
    print('tooltip has a delay before it appears.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
