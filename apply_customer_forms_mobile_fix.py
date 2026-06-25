# -*- coding: utf-8 -*-
"""
Apply: fix the overlapping form fields on mobile for the customer screens.

Root cause: the mobile media query sets `.form-row { flex-direction: column; }`
but leaves `flex-wrap: wrap` on (from the base rule), and children at
`flex: 0 0 100%`. A column-direction + wrap flex container with an indefinite
height wraps items into multiple side-by-side columns instead of stacking them,
producing the diagonal cascade of overlapping labels/inputs. `flex-basis: 100%`
in column mode also resolves against height, compounding it.

Fix (mobile only): force `flex-wrap: nowrap`, change children to
`flex: 0 0 auto; width: 100%; max-width: 100%`, and zero Bootstrap's residual
column padding / row negative-margins so each field is a clean full-width row.

  pages/templates/customer_form.html           (.form-row + col block)
  pages/templates/customer_invoice_form.html   (.form-row + col block; .settings-row + field block)

Desktop layout is untouched. No view/route/migration changes.

Fail-loud: every anchor must appear exactly once in its file or nothing is written.
After running: reload each screen on a narrow viewport.

Run from the repo root:  python apply_customer_forms_mobile_fix.py
"""
import io
import os
import sys

CFORM = os.path.join("pages", "templates", "customer_form.html")
IFORM = os.path.join("pages", "templates", "customer_invoice_form.html")

# --- customer_form.html: .form-row + .col-md-* mobile block ---
CFORM_OLD = '''  .form-row { flex-direction: column; gap: 0; }
  .col-md-4, .col-md-6, .col-md-8, .col-md-12 { flex: 0 0 100%; }'''
CFORM_NEW = '''  .form-row { flex-direction: column; flex-wrap: nowrap; gap: 0; margin-left: 0; margin-right: 0; }
  .col-md-4, .col-md-6, .col-md-8, .col-md-12 { flex: 0 0 auto; width: 100%; max-width: 100%; padding-left: 0; padding-right: 0; }'''

# --- customer_invoice_form.html: .form-row + .col-* mobile block ---
IFORM_ROW_OLD = '''  .form-row { flex-direction: column; gap: 0; }
  .col-4, .col-5, .col-6, .col-7, .col-8, .col-12 { flex: 0 0 100%; }'''
IFORM_ROW_NEW = '''  .form-row { flex-direction: column; flex-wrap: nowrap; gap: 0; margin-left: 0; margin-right: 0; }
  .col-4, .col-5, .col-6, .col-7, .col-8, .col-12 { flex: 0 0 auto; width: 100%; max-width: 100%; padding-left: 0; padding-right: 0; }'''

# --- customer_invoice_form.html: .settings-row + .settings-field mobile block ---
IFORM_SET_OLD = '''  .settings-row { flex-direction: column; gap: 0; }
  .settings-field { flex: 0 0 100%; margin-bottom: 16px; }'''
IFORM_SET_NEW = '''  .settings-row { flex-direction: column; flex-wrap: nowrap; gap: 0; }
  .settings-field { flex: 0 0 auto; width: 100%; max-width: 100%; margin-bottom: 16px; }'''

# file -> list of (label, old, new)
PLAN = {
    CFORM: [("form-row", CFORM_OLD, CFORM_NEW)],
    IFORM: [("form-row", IFORM_ROW_OLD, IFORM_ROW_NEW),
            ("settings-row", IFORM_SET_OLD, IFORM_SET_NEW)],
}


def main():
    # Validate every file + anchor first; write nothing until all pass.
    staged = {}
    problems = []
    for path, edits in PLAN.items():
        if not os.path.exists(path):
            problems.append("  missing file: %s" % path)
            continue
        with io.open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        new_src = src
        for label, old, new in edits:
            c = new_src.count(old)
            if c != 1:
                problems.append("  %s [%s]: anchor found %d time(s) (expected 1)"
                                % (os.path.basename(path), label, c))
                continue
            # brace balance sanity on the replacement
            if new.count("{") != new.count("}"):
                problems.append("  %s [%s]: replacement brace imbalance" % (os.path.basename(path), label))
                continue
            new_src = new_src.replace(old, new, 1)
        staged[path] = (src, new_src)

    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    for path, (src, new_src) in staged.items():
        with io.open(path + ".prebak", "w", encoding="utf-8", newline="") as fh:
            fh.write(src)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_src)
        print("OK: %s (backup %s.prebak)" % (path, path))
    print("done. reload each customer screen on a narrow viewport to verify.")


if __name__ == "__main__":
    main()