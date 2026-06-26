# -*- coding: utf-8 -*-
"""
Option B - Step 1: re-key Physical Invoices view decorators to invoice permissions.

  pages/views/physical_invoices.py
    @permission_required('auth.can_access_tenants', ...) -> can_access_invoices
    @permission_required('auth.can_edit_tenants',   ...) -> can_edit_invoices

Every view in this module is a physical-invoice or customer-invoice view, so all
of them move from the tenant permissions to the existing invoice permissions
(can_access_invoices / can_edit_invoices). No new permission, no migration.

This is the canonical (decorator) security layer. The URL middleware map and the
template gates are handled in later steps.

NOTE: the three @login_required-only PDF/preview views
(render_invoice_preview, render_invoice_for_tenant, render_stored_invoice_pdf)
are deliberately NOT touched here - whether to gate them with can_access_invoices
is a separate decision (Step 1b).

Fail-loud: aborts unless BOTH decorator strings are present and, after the swap,
NO tenant-permission decorator remains in the file.
After running:  python manage.py check

Run from the repo root:  python apply_pi_perms_step1_decorators.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")

OLD_ACCESS = "@permission_required('auth.can_access_tenants', raise_exception=True)"
NEW_ACCESS = "@permission_required('auth.can_access_invoices', raise_exception=True)"
OLD_EDIT = "@permission_required('auth.can_edit_tenants', raise_exception=True)"
NEW_EDIT = "@permission_required('auth.can_edit_invoices', raise_exception=True)"


def main():
    if not os.path.exists(VIEWS):
        sys.exit("ABORTED - missing file: %s" % VIEWS)
    with io.open(VIEWS, "r", encoding="utf-8") as fh:
        src = fh.read()

    n_access = src.count(OLD_ACCESS)
    n_edit = src.count(OLD_EDIT)
    if n_access < 1 or n_edit < 1:
        sys.exit("ABORTED - expected both decorator strings; found access=%d edit=%d; "
                 "nothing written." % (n_access, n_edit))

    new_src = src.replace(OLD_ACCESS, NEW_ACCESS).replace(OLD_EDIT, NEW_EDIT)

    # Safety: no tenant-permission decorator may remain.
    if ("can_access_tenants" in new_src) or ("can_edit_tenants" in new_src):
        sys.exit("ABORTED - a tenant-permission reference still remains after swap; nothing written.")

    try:
        ast.parse(new_src)
    except SyntaxError as e:
        sys.exit("ABORTED - %s does not parse: %s" % (VIEWS, e))

    with io.open(VIEWS + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(VIEWS, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (VIEWS, VIEWS))
    print("     swapped %d access + %d edit decorators -> invoice permissions" % (n_access, n_edit))
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()