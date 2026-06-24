# -*- coding: utf-8 -*-
"""
Apply: add a "Physical Invoices" entry to the Tenants page (navigation).

  pages/templates/tenant.html
    + a "Physical Invoices" secondary button (desktop), after Open Invoices
    + a "Physical Invoices" item in the mobile "More" menu, after Open Invoices

Fail-loud: every anchor must appear exactly once or nothing is written.
Templates need no migration/restart; a browser refresh shows them.

Run from the repo root:  python apply_pi_nav.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "tenant.html")

EDITS = [
    # Desktop secondary button
    ('      <a href="{% url \'open_invoices_report\' %}" class="btn btn-info action-secondary">Open Invoices</a>',
     '      <a href="{% url \'open_invoices_report\' %}" class="btn btn-info action-secondary">Open Invoices</a>\n'
     '      <a href="{% url \'physical_invoice_list\' %}" class="btn btn-info action-secondary">Physical Invoices</a>'),

    # Mobile "More" menu item
    ('''          <a href="{% url 'open_invoices_report' %}" class="action-more-item" role="menuitem">
            <i class="fas fa-file-invoice-dollar"></i> Open Invoices
          </a>''',
     '''          <a href="{% url 'open_invoices_report' %}" class="action-more-item" role="menuitem">
            <i class="fas fa-file-invoice-dollar"></i> Open Invoices
          </a>
          <a href="{% url 'physical_invoice_list' %}" class="action-more-item" role="menuitem">
            <i class="fas fa-file-invoice"></i> Physical Invoices
          </a>'''),
]


def main():
    if not os.path.exists(TPL):
        sys.exit("MISSING FILE: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
        src = fh.read()
    problems = []
    for i, (old, _new) in enumerate(EDITS, 1):
        n = src.count(old)
        if n != 1:
            problems.append("  edit %d: anchor found %d time(s) (expected 1)" % (i, n))
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    new_src = src
    for old, new in EDITS:
        new_src = new_src.replace(old, new, 1)
    with io.open(TPL + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (TPL, TPL))
    print("done. refresh the Tenants page to see the button.")


if __name__ == "__main__":
    main()