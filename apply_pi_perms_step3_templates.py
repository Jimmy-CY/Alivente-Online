# -*- coding: utf-8 -*-
"""
Option B - Step 3: re-key template permission guards to invoice permissions.

For each physical-invoice / customer template, swap the guard tokens:
    perms.auth.can_access_tenants -> perms.auth.can_access_invoices
    perms.auth.can_edit_tenants   -> perms.auth.can_edit_invoices

Files:
    pages/templates/physical_invoice_list.html
    pages/templates/physical_invoice_edit.html
    pages/templates/customer_list.html
    pages/templates/customer_invoice_form.html

(customer_form.html has no internal perms guards and is intentionally not touched.)

Every can_*_tenants guard in these templates is physical-invoice/customer related,
so a whole-token swap is correct. URL names like {% url 'tenant' %} are NOT touched
(only the 'perms.auth.can_*_tenants' tokens are).

Fail-loud: a file with zero matching guards aborts the WHOLE run (writes nothing),
since that signals an unexpected state. After swapping, no tenant-permission guard
token may remain in any target file.

Run from the repo root:  python apply_pi_perms_step3_templates.py
"""
import io
import os
import sys

FILES = [
    os.path.join("pages", "templates", "physical_invoice_list.html"),
    os.path.join("pages", "templates", "physical_invoice_edit.html"),
    os.path.join("pages", "templates", "customer_list.html"),
    os.path.join("pages", "templates", "customer_invoice_form.html"),
]

SWAPS = [
    ("perms.auth.can_access_tenants", "perms.auth.can_access_invoices"),
    ("perms.auth.can_edit_tenants", "perms.auth.can_edit_invoices"),
]


def main():
    # ---- Pass 1: read all, validate, compute new content. Write nothing yet. ----
    planned = []  # (path, original, new, n_swaps)
    problems = []
    for path in FILES:
        if not os.path.exists(path):
            problems.append("  missing file: %s" % path)
            continue
        with io.open(path, "r", encoding="utf-8") as fh:
            src = fh.read()

        n = sum(src.count(old) for old, _new in SWAPS)
        if n == 0:
            # Either already swapped or the file is not what we expect.
            if ("perms.auth.can_access_invoices" in src) or ("perms.auth.can_edit_invoices" in src):
                problems.append("  %s: already uses invoice guards (count 0) - looks already done" % path)
            else:
                problems.append("  %s: found 0 tenant guard tokens (unexpected)" % path)
            continue

        new = src
        for old, repl in SWAPS:
            new = new.replace(old, repl)

        if ("perms.auth.can_access_tenants" in new) or ("perms.auth.can_edit_tenants" in new):
            problems.append("  %s: a tenant guard token still remains after swap" % path)
            continue

        planned.append((path, src, new, n))

    if problems or len(planned) != len(FILES):
        sys.exit("ABORTED - nothing written:\n" + "\n".join(problems or ["  (incomplete plan)"]))

    # ---- Pass 2: all good - back up and write. ----
    for path, src, new, n in planned:
        with io.open(path + ".prebak", "w", encoding="utf-8", newline="") as fh:
            fh.write(src)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
        print("OK: %s  (%d guard token(s) swapped, backup %s.prebak)" % (path, n, path))

    print("done. (templates - no manage.py check needed; restart not required for guards)")


if __name__ == "__main__":
    main()