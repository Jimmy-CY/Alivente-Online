# -*- coding: utf-8 -*-
"""
Apply: fix the Physical Invoices list header buttons overflowing on mobile.

  pages/templates/physical_invoice_list.html  (mobile media query)
    ~ .page-action-buttons: flex-wrap nowrap -> wrap (let buttons flow to a
      second line instead of overflowing off-screen)
    + .action-secondary: mobile sizing (flex: 1 1 auto, fixed height, single-line
      with ellipsis) so the three teal buttons share each row and wrap cleanly;
      the Back arrow stays compact (its existing 44px rule is unchanged)

Four header buttons (Help, New Customer Invoice, Manage Customers, Back) cannot
fit on one ~386px line; wrapping lays them out as e.g. two rows. Desktop layout
is untouched.

Fail-loud: the anchor must appear exactly once or nothing is written.
Run from the repo root:  python apply_pi_list_header_mobile.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "physical_invoice_list.html")

OLD = '''  .page-action-buttons {
    display: flex; flex-direction: row; gap: 8px; width: 100%;
    flex-wrap: nowrap; align-items: stretch; margin-bottom: 14px;
    justify-content: flex-end;
  }
  .action-back {'''

NEW = '''  .page-action-buttons {
    display: flex; flex-direction: row; gap: 8px; width: 100%;
    flex-wrap: wrap; align-items: stretch; margin-bottom: 14px;
    justify-content: flex-end;
  }
  .action-secondary {
    flex: 1 1 auto; min-width: 0; height: 38px;
    display: flex; align-items: center; justify-content: center;
    padding: 0 10px; font-size: 13px; white-space: nowrap; margin: 0;
    overflow: hidden; text-overflow: ellipsis;
  }
  .action-back {'''


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
        src = fh.read()

    if ".action-secondary {" in src.split("@media", 1)[-1]:
        # crude guard: an action-secondary rule already exists in the mobile block
        # (only abort if our specific flex sizing is already present)
        if "flex: 1 1 auto; min-width: 0; height: 38px;" in src:
            sys.exit("ABORTED - mobile .action-secondary sizing already present in %s" % TPL)

    n = src.count(OLD)
    if n != 1:
        sys.exit("ABORTED - anchor found %d time(s) (expected 1); nothing written." % n)
    if (NEW.count("{") - OLD.count("{")) != (NEW.count("}") - OLD.count("}")):
        sys.exit("ABORTED - replacement changes overall brace balance.")

    new_src = src.replace(OLD, NEW, 1)
    with io.open(TPL + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (TPL, TPL))
    print("done. HARD-refresh the list on a narrow viewport (Ctrl+Shift+R).")


if __name__ == "__main__":
    main()