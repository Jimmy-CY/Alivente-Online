# -*- coding: utf-8 -*-
"""
Apply: fix the read-only gate on the customer-invoice form.

  pages/templates/customer_invoice_form.html
    ~ {% with editable=is_editable|default:True %}
      -> {% with editable=is_editable|default_if_none:True %}

Root cause: Django's `default` filter substitutes on ANY falsy value, so for a
sent/approved invoice is_editable=False became editable=True, leaving every
field editable. `default_if_none` substitutes only for None, so False stays
False and the form locks correctly (and the readonly grey styling then shows).

Fail-loud: the anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_customer_invoice_editable_fix.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "customer_invoice_form.html")

OLD = "{% with editable=is_editable|default:True %}"
NEW = "{% with editable=is_editable|default_if_none:True %}"


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
        src = fh.read()

    n = src.count(OLD)
    if n != 1:
        sys.exit("ABORTED - anchor found %d time(s) (expected 1); no changes written." % n)

    new_src = src.replace(OLD, NEW, 1)

    with io.open(TPL + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (TPL, TPL))
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()