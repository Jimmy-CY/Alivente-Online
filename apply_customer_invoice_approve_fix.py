# -*- coding: utf-8 -*-
"""
Apply: make approve / un-approve messages work for customer (non-tenant) invoices.

  pages/views/physical_invoices.py
    + a small helper _pi_who(pi): tenant name, or the bill_* snapshot name for a
      customer invoice.
    ~ physical_invoice_approve / physical_invoice_unapprove success messages use
      _pi_who(pi) instead of pi.tenant.tenant_name (which is None -> 500 for a
      customer invoice).

The approve/un-approve actions themselves were already type-agnostic (status
only); only the confirmation message assumed a tenant.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_customer_invoice_approve_fix.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")

# 1) Insert the helper just before _redirect_after_pi_action (which both approve
#    and un-approve already sit next to).
HELPER_ANCHOR = "def _redirect_after_pi_action(request, pi):"
HELPER_NEW = '''def _pi_who(pi):
    """Display name for an invoice: the tenant's name, or the customer snapshot
    name for a customer (non-tenant) invoice."""
    if getattr(pi, "tenant_id", None):
        return pi.tenant.tenant_name
    return pi.bill_name or "customer"


def _redirect_after_pi_action(request, pi):'''

# 2) approve message
APPROVE_OLD = '        messages.success(request, f"Invoice for {pi.tenant.tenant_name} approved.")'
APPROVE_NEW = '        messages.success(request, f"Invoice for {_pi_who(pi)} approved.")'

# 3) un-approve message
UNAPPROVE_OLD = '        messages.success(request, f"Invoice for {pi.tenant.tenant_name} moved back to draft.")'
UNAPPROVE_NEW = '        messages.success(request, f"Invoice for {_pi_who(pi)} moved back to draft.")'

EDITS = [
    (HELPER_ANCHOR, HELPER_NEW),
    (APPROVE_OLD, APPROVE_NEW),
    (UNAPPROVE_OLD, UNAPPROVE_NEW),
]


def main():
    if not os.path.exists(VIEWS):
        sys.exit("ABORTED - missing file: %s" % VIEWS)
    with io.open(VIEWS, "r", encoding="utf-8") as fh:
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