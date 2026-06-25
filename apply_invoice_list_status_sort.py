# -*- coding: utf-8 -*-
"""
Apply: group the Physical Invoices list by status, then sort within each group.

  pages/views/physical_invoices.py  (physical_invoice_list)
    ~ replace the two-pass date/name sort with a single status-grouped key:
        order:   Draft  ->  Approved  ->  Sent
        Draft / Approved : newest date first (period_year, period_month,
                           invoice_date DESC), then name A->Z
        Sent             : PR number DESCENDING (highest number first)

The composite key is all-ascending with descending components negated, so one
sorted() call produces the full ordering (no second pass needed). The sent
ordering uses the trailing integer of the invoice number, so PR-0100 sorts
above PR-0099 numerically (not as strings).

Fail-loud: the anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_invoice_list_status_sort.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")

# Anchor = the current two-pass sort (from the previous sort change).
OLD = '''    # Order newest-first by date, then name A->Z within the same date.
    # Two-pass stable sort: name ascending first, then date descending.
    def _name_key(pi):
        return (pi.tenant.tenant_name if pi.tenant_id else (pi.bill_name or "")).lower()

    def _date_key(pi):
        return (pi.period_year, pi.period_month, pi.invoice_date or date.min)

    qs = sorted(qs, key=_name_key)
    qs = sorted(qs, key=_date_key, reverse=True)'''

NEW = '''    # Group by status (Draft -> Approved -> Sent); sort within each group.
    #   Draft / Approved : newest date first, then name A->Z
    #   Sent             : PR number descending (highest first)
    # Single composite key, all ascending, with descending parts negated.
    _status_rank = {
        PhysicalInvoice.STATUS_DRAFT: 0,
        PhysicalInvoice.STATUS_APPROVED: 1,
        PhysicalInvoice.STATUS_SENT: 2,
    }

    def _trailing_int(value):
        digits = ""
        for ch in reversed((value or "").strip()):
            if ch.isdigit():
                digits = ch + digits
            elif digits:
                break
        return int(digits) if digits else 0

    def _sort_key(pi):
        grp = _status_rank.get(pi.status, 99)
        name = (pi.tenant.tenant_name if pi.tenant_id else (pi.bill_name or "")).lower()
        if pi.status == PhysicalInvoice.STATUS_SENT:
            # PR number descending; date/name not needed (numbers are unique).
            return (grp, -_trailing_int(pi.invoice_number), 0, "")
        # Draft / Approved: date descending, then name ascending.
        idx = pi.period_year * 12 + pi.period_month
        day = (pi.invoice_date or date.min).toordinal()
        return (grp, 0, -(idx * 1000 + day), name)

    qs = sorted(qs, key=_sort_key)'''


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