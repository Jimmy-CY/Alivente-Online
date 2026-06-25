# -*- coding: utf-8 -*-
"""
Apply: two read-only fixes to the customer-invoice form.

  pages/templates/customer_invoice_form.html
    1. Status-aware lock banner: a SENT invoice says it is final and cannot be
       changed (un-approve only applies to an APPROVED, not-yet-sent invoice).
    2. Visually grey out the whole form when not editable: readonly inputs /
       textareas and disabled selects get a muted grey style, so a sent/approved
       invoice clearly reads as locked (the fields were already functionally
       read-only; this makes that visible).

Single-file, surgical. No view/route/migration changes.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check  (template-only)

Run from the repo root:  python apply_customer_invoice_form_locked.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "customer_invoice_form.html")

EDITS = [
    # 1) status-aware banner message
    ("    Un-approve it first to make changes.",
     "    {% if pi.status == 'approved' %}Un-approve it first to make changes."
     "{% else %}Sent invoices are final and cannot be changed.{% endif %}"),

    # 2) grey out readonly/disabled controls (covers the whole locked form)
    ("textarea.form-control { resize: vertical; }",
     "textarea.form-control { resize: vertical; }\n"
     ".form-control[readonly], .form-control:disabled,\n"
     ".line-input[readonly], .line-input:disabled {\n"
     "  background-color: #e9ecef; color: #6c757d; cursor: not-allowed; opacity: 1;\n"
     "}"),
]


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
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
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()