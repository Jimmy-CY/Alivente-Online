# -*- coding: utf-8 -*-
"""
Apply: editable invoice number on the edit screen (the #2 request) - VIEW side.

  pages/views/physical_invoices.py
    in physical_invoice_edit's POST, after recalc_totals(): save a manual
    invoice_number from the form (blank -> None, so the send cron auto-assigns).

Pairs with the corrected physical_invoice_edit.html (delivered separately),
which adds the Invoice Number input.

Fail-loud: the anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_pi_invoice_number.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")

EDITS = [
    ('''            pi.recalc_totals()

        messages.success(''',
     '''            pi.recalc_totals()

        # Manual invoice number override (blank = auto-assign on send).
        manual_number = (request.POST.get("invoice_number") or "").strip()[:32]
        pi.invoice_number = manual_number or None
        pi.save(update_fields=["invoice_number", "updated_at"])

        messages.success('''),
]


def main():
    if not os.path.exists(VIEWS):
        sys.exit("MISSING FILE: %s" % VIEWS)
    with io.open(VIEWS, "r", encoding="utf-8") as fh:
        src = fh.read()
    for i, (old, _new) in enumerate(EDITS, 1):
        n = src.count(old)
        if n != 1:
            sys.exit("ABORTED - edit %d: anchor found %d time(s) (expected 1)" % (i, n))

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
    print("done. next: check")


if __name__ == "__main__":
    main()