# -*- coding: utf-8 -*-
"""
Apply: Phase 5a — guard the monthly send cron so it only ever processes TENANT
invoices. Customer (non-tenant) invoices are sent on demand via the Send-now
button (Phase 5b), never by this daily batch.

  pages/management/commands/send_physical_invoices.py
    + a thin module-level helper _tenant_batch(year, month, statuses) that wraps
      month_batch and drops customer invoices (tenant is None).
    ~ the three month_batch(...) call sites (numbering, send loop, back-fill)
      switch to _tenant_batch(...).

Why a wrapper here rather than editing month_batch: month_batch is shared with
preview_batch_numbers (the list preview), which legitimately sees both invoice
types. The "monthly cron is tenant-only" rule belongs in the cron, not buried in
the low-level helper.

Without this guard, an APPROVED customer invoice dated in the open month would be
numbered + emailed by the cron (to a null tenant_email), which is wrong.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_send_cron_tenant_guard.py
"""
import ast
import io
import os
import sys

CRON = os.path.join("pages", "management", "commands", "send_physical_invoices.py")

# 1) Add the wrapper right after the import that brings month_batch in.
IMP_OLD = "from pages.services.physical_invoice_numbering import month_batch, suggested_next_number"
IMP_NEW = (IMP_OLD + "\n\n\n"
           "def _tenant_batch(year, month, statuses=None):\n"
           '    """month_batch filtered to TENANT invoices only. Customer (non-tenant)\n'
           "    invoices are sent on demand, never by this monthly cron.\"\"\"\n"
           "    return [pi for pi in month_batch(year, month, statuses=statuses)\n"
           "            if pi.tenant_id is not None]")

# 2) numbering pass
S1_OLD = '        approved = month_batch(year, month, statuses=("approved",))  # A->Z, then tenant_id'
S1_NEW = '        approved = _tenant_batch(year, month, statuses=("approved",))  # A->Z, then tenant_id'

# 3) send loop
S2_OLD = '''        # 2) Send approved-not-sent invoices (A->Z within the period).
        approved = month_batch(year, month, statuses=("approved",))'''
S2_NEW = '''        # 2) Send approved-not-sent invoices (A->Z within the period).
        approved = _tenant_batch(year, month, statuses=("approved",))'''

# 4) back-fill loop
S3_OLD = '        for pi in month_batch(year, month, statuses=("sent",)):'
S3_NEW = '        for pi in _tenant_batch(year, month, statuses=("sent",)):'

EDITS = [
    (IMP_OLD, IMP_NEW),
    (S1_OLD, S1_NEW),
    (S2_OLD, S2_NEW),
    (S3_OLD, S3_NEW),
]


def main():
    if not os.path.exists(CRON):
        sys.exit("ABORTED - missing file: %s" % CRON)
    with io.open(CRON, "r", encoding="utf-8") as fh:
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
        sys.exit("ABORTED - %s does not parse: %s" % (CRON, e))

    with io.open(CRON + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(CRON, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (CRON, CRON))
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()