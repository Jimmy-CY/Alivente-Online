# -*- coding: utf-8 -*-
"""
Apply: show "(on send)" for an unsent TENANT invoice on its edit screen.

  pages/views/physical_invoices.py  (physical_invoice_edit, GET branch)
    - drop the provisional preview lookup
    ~ "number": pi.invoice_number or "(on send)"

This matches the list: the subtitle and the summary NUMBER field now show
"(on send)" until the invoice is actually sent, instead of a provisional preview
that looked like an assigned (and possibly duplicate) number.

Fail-loud: the anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_tenant_edit_onsend.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")

OLD = '''    provisional = preview_batch_numbers(
        pi.period_year, pi.period_month,
        statuses=(PhysicalInvoice.STATUS_DRAFT, PhysicalInvoice.STATUS_APPROVED))
    context = {
        "pi": pi,
        "lines": pi.lines.all(),
        "number": pi.invoice_number or provisional.get(pi.pk, "\\u2014"),'''
NEW = '''    context = {
        "pi": pi,
        "lines": pi.lines.all(),
        "number": pi.invoice_number or "(on send)",'''


def main():
    if not os.path.exists(VIEWS):
        sys.exit("ABORTED - missing file: %s" % VIEWS)
    with io.open(VIEWS, "r", encoding="utf-8") as fh:
        src = fh.read()

    n = src.count(OLD)
    if n != 1:
        sys.exit("ABORTED - anchor found %d time(s) (expected 1); no changes written." % n)

    new_src = src.replace(OLD, NEW, 1)
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        sys.exit("ABORTED - %s does not parse: %s" % (VIEWS, e))

    with io.open(VIEWS + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(VIEWS, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (VIEWS, VIEWS))
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()