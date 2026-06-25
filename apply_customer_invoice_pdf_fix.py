# -*- coding: utf-8 -*-
"""
Apply: render the PDF for customer (non-tenant) invoices.

  pages/views/physical_invoices.py  (build_context_from_invoice)
    ~ branch on invoice type: tenant invoice keeps the existing _billing_block
      path; customer invoice builds the billing block from the frozen bill_*
      snapshot on the invoice instead of from a (non-existent) tenant profile.

This fixes "Unable to display this document" when viewing a customer invoice:
render_stored_invoice_pdf -> build_context_from_invoice was calling
_billing_block(pi.tenant) with pi.tenant == None, which raised. The PDF endpoint
itself (physical_invoice_pdf) already serves both types, so no URL/template
change is needed.

Fail-loud: the anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_customer_invoice_pdf_fix.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")

OLD = '''    pi = physical_invoice
    customer, customer_id = _billing_block(pi.tenant)'''
NEW = '''    pi = physical_invoice
    if pi.tenant_id is not None:
        customer, customer_id = _billing_block(pi.tenant)
    else:
        # Customer (non-tenant) invoice: build the billing block from the frozen
        # bill_* snapshot stored on the invoice (never from a live record).
        address_lines = [ln.strip() for ln in (pi.bill_address or "").splitlines() if ln.strip()]
        customer = {
            "name": pi.bill_name or "",
            "address_lines": address_lines,
            "tel": pi.bill_tel or "",
        }
        customer_id = pi.bill_customer_label or pi.bill_name or ""'''


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