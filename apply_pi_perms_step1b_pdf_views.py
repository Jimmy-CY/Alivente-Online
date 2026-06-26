# -*- coding: utf-8 -*-
"""
Option B - Step 1b: gate the three render/preview views with can_access_invoices.

  pages/views/physical_invoices.py
    render_invoice_preview      (physical-invoices/preview/)        @login_required only -> + can_access_invoices
    render_invoice_for_tenant   (currently UNROUTED)                @login_required only -> + can_access_invoices
    render_stored_invoice_pdf   (physical-invoices/<id>/pdf/)       @login_required only -> + can_access_invoices

These serve real invoice content (a stored PDF, a tenant preview, a sample).
Adding can_access_invoices makes the canonical (decorator) layer consistent with
every other view in the module; the middleware change in Step 2 covers the same
paths as a safety net.

Fail-loud: each of the three @login_required-only defs must be present exactly
once and must not already carry a permission_required. Aborts writing nothing
otherwise. ast.parse validates the result.

After running:  python manage.py check
Run from the repo root:  python apply_pi_perms_step1b_pdf_views.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
PERM = "@permission_required('auth.can_access_invoices', raise_exception=True)"

TARGETS = [
    ("@login_required\ndef render_invoice_preview(request):",
     "@login_required\n%s\ndef render_invoice_preview(request):" % PERM),
    ("@login_required\ndef render_invoice_for_tenant(request, tenant_id):",
     "@login_required\n%s\ndef render_invoice_for_tenant(request, tenant_id):" % PERM),
    ("@login_required\ndef render_stored_invoice_pdf(request, physical_invoice_id):",
     "@login_required\n%s\ndef render_stored_invoice_pdf(request, physical_invoice_id):" % PERM),
]


def main():
    if not os.path.exists(VIEWS):
        sys.exit("ABORTED - missing file: %s" % VIEWS)
    with io.open(VIEWS, "r", encoding="utf-8") as fh:
        src = fh.read()

    problems = []
    for old, _new in TARGETS:
        c = src.count(old)
        if c != 1:
            problems.append("  anchor found %d time(s) (expected 1): %s" % (c, old.splitlines()[-1]))
    if problems:
        sys.exit("ABORTED - nothing written:\n" + "\n".join(problems))

    new_src = src
    for old, new in TARGETS:
        new_src = new_src.replace(old, new, 1)

    # The three views must now each carry the permission decorator.
    if new_src.count(PERM) < src.count(PERM) + 3:
        sys.exit("ABORTED - did not add 3 permission decorators; nothing written.")

    try:
        ast.parse(new_src)
    except SyntaxError as e:
        sys.exit("ABORTED - %s does not parse: %s" % (VIEWS, e))

    with io.open(VIEWS + ".prebak1b", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(VIEWS, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak1b)" % (VIEWS, VIEWS))
    print("     gated render_invoice_preview / render_invoice_for_tenant / render_stored_invoice_pdf")
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()