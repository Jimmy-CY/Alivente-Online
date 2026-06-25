# -*- coding: utf-8 -*-
"""
Apply: order the Physical Invoices list newest-first by date, then name A->Z.

  pages/views/physical_invoices.py  (physical_invoice_list)
    ~ replace the single name-only sort with a two-pass stable sort:
        1) name A->Z (tie-break)
        2) (period_year, period_month, invoice_date) DESC (primary)
      Stable sort means equal-date rows keep their A->Z order, giving:
      newest date first; within the same date, name ascending. Uniform across
      tenant and customer invoices; a missing invoice_date sorts as date.min.

Fail-loud: the anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_invoice_list_sort.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")

OLD = '''    # Order by display name across both kinds (tenant name or customer snapshot name).
    qs = sorted(
        qs,
        key=lambda pi: (pi.tenant.tenant_name if pi.tenant_id else (pi.bill_name or "")).lower())'''
NEW = '''    # Order newest-first by date, then name A->Z within the same date.
    # Two-pass stable sort: name ascending first, then date descending.
    def _name_key(pi):
        return (pi.tenant.tenant_name if pi.tenant_id else (pi.bill_name or "")).lower()

    def _date_key(pi):
        return (pi.period_year, pi.period_month, pi.invoice_date or date.min)

    qs = sorted(qs, key=_name_key)
    qs = sorted(qs, key=_date_key, reverse=True)'''


def main():
    if not os.path.exists(VIEWS):
        sys.exit("ABORTED - missing file: %s" % VIEWS)
    with io.open(VIEWS, "r", encoding="utf-8") as fh:
        src = fh.read()

    n = src.count(OLD)
    if n != 1:
        sys.exit("ABORTED - anchor found %d time(s) (expected 1); no changes written." % n)

    new_src = src.replace(OLD, NEW, 1)
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