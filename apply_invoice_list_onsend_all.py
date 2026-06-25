# -*- coding: utf-8 -*-
"""
Apply: show "(on send)" for every UNSENT invoice (tenant + customer) in the list.

Numbers are assigned at send from the shared counter, so an unsent invoice does
not yet own a number. Previously tenant drafts showed a provisional preview,
which looked like a locked number and could appear to collide with numbers
already issued to sent customer invoices. Showing "(on send)" for all unsent
invoices makes the list unambiguous: only a SENT invoice displays a real PR
number.

  pages/views/physical_invoices.py  (physical_invoice_list)
    - remove the now-unused single-month provisional block
    - remove the now-dead `y, m = ...` line it depended on
    ~ row "number": pi.invoice_number or "(on send)"  (both invoice types)

Note: preview_batch_numbers is left imported (now unused here) to keep this edit
minimal; it can be dropped in a later import-hygiene sweep.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_invoice_list_onsend_all.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")

# 1) remove the dead y, m line (it existed only for provisional numbering)
YM_OLD = '''    single_month = (from_idx == to_idx)
    y, m = from_first.year, from_first.month  # used for single-month provisional numbering

    base = PhysicalInvoice.objects.annotate('''
YM_NEW = '''    single_month = (from_idx == to_idx)

    base = PhysicalInvoice.objects.annotate('''

# 2) remove the provisional block
PROV_OLD = '''    if single_month:
        provisional = preview_batch_numbers(
            y, m, statuses=(PhysicalInvoice.STATUS_DRAFT, PhysicalInvoice.STATUS_APPROVED))
    else:
        provisional = {}

'''
PROV_NEW = ''

# 3) row number: any unsent invoice -> "(on send)"
ROW_OLD = '            "number": pi.invoice_number or ("(on send)" if is_customer else provisional.get(pi.pk, "\\u2014")),'
ROW_NEW = '            "number": pi.invoice_number or "(on send)",'

EDITS = [(YM_OLD, YM_NEW), (PROV_OLD, PROV_NEW), (ROW_OLD, ROW_NEW)]


def main():
    if not os.path.exists(VIEWS):
        sys.exit("ABORTED - missing file: %s" % VIEWS)
    with io.open(VIEWS, "r", encoding="utf-8") as fh:
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