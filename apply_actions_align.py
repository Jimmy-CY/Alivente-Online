#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Actions heading sits over its buttons on the two invoice screens.

WHAT WENT WRONG. base.html centres an actions column with a PAIR of rules -
one for the cells, one for the heading:

    .alv-table .desktop-action-cell, .alv-table th.desktop-action-cell { text-align: center }
    .alv-table .cell-actions,        .alv-table th.cell-actions        { text-align: center; white-space: nowrap }

physical_invoice_list already had ONE actions column before this round, so the
migration skipped the collapse - and the alignment classes come WITH the
collapse. Its cells were centred and its `<th>` had no class at all, so the
heading stayed left of the buttons it labels. Suppliers, Properties and
Tenants all carry `class="desktop-action-cell cell-actions"` on that heading;
these two did not.

customer_list got `cell-actions` but not `desktop-action-cell`, which centres
it correctly but leaves it out of step with the other four - and
`.desktop-action-cell { display: none !important }` is what keeps the heading
out of the mobile card view.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT  = os.path.dirname(os.path.abspath(__file__))
TPL   = os.path.join(ROOT, 'pages', 'templates')
CHECK = '--check' in sys.argv

HOUSE = 'desktop-action-cell cell-actions'

EDITS = [
    ('physical_invoice_list.html',
     'the Actions heading gets the house classes',
     '<th style="width: 14%">Actions</th>',
     '<th class="%s" style="width: 14%%">Actions</th>' % HOUSE),
    ('physical_invoice_list.html',
     '  and its cell says it is the actions cell',
     '<td data-label="Actions" class="desktop-action-cell pi-actions-cell">',
     '<td data-label="Actions" class="desktop-action-cell cell-actions pi-actions-cell">'),
    ('customer_list.html',
     'the Actions heading matches the other four pages',
     '<th class="cell-actions" style="width: 14%">Actions</th>',
     '<th class="%s" style="width: 14%%">Actions</th>' % HOUSE),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def main():
    changed = 0
    for fname in ('physical_invoice_list.html', 'customer_list.html'):
        p = os.path.join(TPL, fname)
        src = read(p)
        out, n, skipped = src, 0, 0
        for f, what, old, new in EDITS:
            if f != fname:
                continue
            if old not in out:
                if new in out:
                    skipped += 1          # already applied
                    continue
                sys.exit('! %s: anchor for "%s" not found.\n    %s'
                         % (fname, what.strip(), old[:90]))
            if out.count(old) != 1:
                sys.exit('! %s: "%s" matched %d times, expected 1'
                         % (fname, what.strip(), out.count(old)))
            out = out.replace(old, new, 1)
            n += 1
        if not n:
            print('  %-28s already aligned (%d edit(s) already in place)'
                  % (fname, skipped))
            continue

        # ---- self-checks ------------------------------------------------
        bad = []
        th = re.search(r'<th[^>]*>[^<]*Actions[^<]*</th>', out)
        if not th:
            bad.append('the Actions heading vanished')
        else:
            for cls in ('desktop-action-cell', 'cell-actions'):
                if cls not in th.group(0):
                    bad.append('the heading is missing %s' % cls)
        # the heading and the cell must agree, or one centres and one does not
        td = re.search(r'<td[^>]*data-label="Actions"[^>]*>', out)
        if td and 'cell-actions' not in td.group(0):
            bad.append('the cell is missing cell-actions')
        for k, rx in (('<th', r'<th\b'), ('<td', r'<td\b'),
                      ('{% if', r'\{%\s*if\b'), ('{% url', r'\{%\s*url ')):
            if len(re.findall(rx, src)) != len(re.findall(rx, out)):
                bad.append('%s count changed' % k)
        if bad:
            sys.exit('! %s self-check FAILED, nothing written:\n   - %s'
                     % (fname, '\n   - '.join(bad)))

        print('  %-28s %d edit(s)' % (fname, n))
        if not CHECK:
            b = p + '.bak_actionsalign'
            if not os.path.exists(b):
                shutil.copy2(p, b)
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(out)
        changed += 1
    print('\n  %d file(s) %s' % (changed, 'would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
