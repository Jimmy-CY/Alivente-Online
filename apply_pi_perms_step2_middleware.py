# -*- coding: utf-8 -*-
"""
Option B - Step 2: add Physical Invoices / Invoice Customers to the middleware map.

  pages/middleware.py  (ModuleAccessMiddleware.url_permission_map, INVOICES block)
    + ('physical-invoices', 'auth.can_access_invoices')
    + ('invoice-customers', 'auth.can_access_invoices')

Every physical-invoice route is under  physical-invoices/...  and every customer
route under  invoice-customers/...  (confirmed from urls.py), so these two
prefixes cover the whole section. Neither prefix is matched by any earlier rule
(they do not start with 'invoices'), so placement in the INVOICES block is safe;
first-match-wins ordering is unaffected.

This is the coarse access gate (can_access_invoices). Edit-level actions remain
gated by the can_edit_invoices view decorators. It also gives non-permitted users
the friendly Access-Denied page instead of a bare 403.

Fail-loud: the INVOICES anchor block must appear exactly once and must not already
contain the new prefixes. ast.parse validates the result.

After running:  python manage.py check
Run from the repo root:  python apply_pi_perms_step2_middleware.py
"""
import ast
import io
import os
import sys

MW = os.path.join("pages", "middleware.py")

OLD = """            # ---------- INVOICES ----------
            ('invoices', 'auth.can_access_invoices'),
            ('invoices_commit', 'auth.can_access_invoices'),
            ('open_invoices', 'auth.can_access_invoices'),"""

NEW = """            # ---------- INVOICES ----------
            ('invoices', 'auth.can_access_invoices'),
            ('invoices_commit', 'auth.can_access_invoices'),
            ('open_invoices', 'auth.can_access_invoices'),
            # Physical Invoices + Invoice Customers (re-homed from Tenants).
            # All routes live under these two prefixes (see urls.py).
            ('physical-invoices', 'auth.can_access_invoices'),
            ('invoice-customers', 'auth.can_access_invoices'),"""


def main():
    if not os.path.exists(MW):
        sys.exit("ABORTED - missing file: %s" % MW)
    with io.open(MW, "r", encoding="utf-8") as fh:
        src = fh.read()

    if ("physical-invoices" in src) or ("invoice-customers" in src):
        sys.exit("ABORTED - middleware already references the new prefixes; nothing written.")

    c = src.count(OLD)
    if c != 1:
        sys.exit("ABORTED - INVOICES anchor block found %d time(s) (expected 1); nothing written." % c)

    new_src = src.replace(OLD, NEW, 1)

    try:
        ast.parse(new_src)
    except SyntaxError as e:
        sys.exit("ABORTED - %s does not parse: %s" % (MW, e))

    with io.open(MW + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(MW, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (MW, MW))
    print("     added physical-invoices + invoice-customers -> can_access_invoices")
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()