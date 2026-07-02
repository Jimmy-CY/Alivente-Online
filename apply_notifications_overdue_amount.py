"""
Apply: correct the amount shown in the Home "Today" panel's Overdue Invoices
modal (and the notifications.html dashboard, which shares the same data).

Root cause: pages/views/notifications_dashboard.py :: get_overdue_invoices
selects tenant.tenant_rent and returns it as the row amount. That's bare rent
-- it ignores the stored invoice.invoice_amount, which already holds the
correct billed figure (physical-invoice total for physical tenants; rent +
communal fees for tenants with Bill Communal Fees on). Every other read path
(Open Invoices list, Debtors report) already coalesces; this one didn't.

Fix (three edits to get_overdue_invoices only):
  1. SELECT invoice.invoice_amount as well  -> row[7]
  2. compute effective_amount = invoice_amount if not None else tenant_rent
     (mirrors invoices.effective_amount and the report's COALESCE)
  3. return that effective amount under the existing 'tenant_rent' key, which
     is what the modal's Amount column reads -- so no template/JS change.

Fail-loud: every anchor must appear exactly once or NOTHING is written. The
result is ast-parsed before writing. Line endings are normalised for matching
and the file's original endings (CRLF) restored on write, so the git diff
shows only these three edits.

Run from the repo root:  python apply_notifications_overdue_amount.py
"""
import ast
import os
import sys

PATH = os.path.join("pages", "views", "notifications_dashboard.py")

EDITS = [
    # 1 -- add invoice_amount to the SELECT (becomes row[7])
    ("""               tenant.tenant_payment_terms, tenant.tenant_rent,
               invoice.invoice_date, invoice.invoice_id
        FROM railway.invoice""",
     """               tenant.tenant_payment_terms, tenant.tenant_rent,
               invoice.invoice_date, invoice.invoice_id, invoice.invoice_amount
        FROM railway.invoice"""),

    # 2 -- read invoice_amount and derive the effective (billed) amount
    ("""        tenant_rent = row[4]
        invoice_date = row[5]
        invoice_id = row[6]
""",
     """        tenant_rent = row[4]
        invoice_date = row[5]
        invoice_id = row[6]
        # Effective billed amount: prefer the stored per-invoice amount (the
        # physical-invoice total, or rent + communal fees when Bill Communal
        # Fees is on) and fall back to bare rent only when nothing was stored.
        # Mirrors invoices.effective_amount and the daily report's COALESCE.
        invoice_amount = row[7]
        effective_amount = invoice_amount if invoice_amount is not None else tenant_rent
"""),

    # 3 -- surface the effective amount under the key the modal already reads
    ("""                'tenant_rent': tenant_rent,""",
     """                'tenant_rent': effective_amount,"""),
]


def main():
    if not os.path.isfile(PATH):
        sys.exit(f"ABORT: {PATH} not found (run from repo root).")

    with open(PATH, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()
    crlf = "\r\n" in raw
    norm = raw.replace("\r\n", "\n")

    problems = []
    for old, new in EDITS:
        c = norm.count(old)
        if c != 1:
            problems.append(f"anchor found {c}x (expected 1): {old[:55]!r}...")
        if new in norm:
            problems.append(f"replacement already present: {new[:55]!r}...")
    if problems:
        print("ABORT -- nothing written:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    out = norm
    for old, new in EDITS:
        out = out.replace(old, new)

    # Validate the result is still valid Python before touching disk.
    try:
        ast.parse(out)
    except SyntaxError as e:
        sys.exit(f"ABORT: result would not parse ({e}); nothing written.")

    if crlf:
        out = out.replace("\n", "\r\n")

    with open(PATH + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(raw)
    with open(PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)

    print(f"OK: {PATH} updated (overdue modal uses effective amount).  "
          f"Endings: {'CRLF' if crlf else 'LF'} preserved.")
    print(f"Backup: {PATH}.prebak")
    print("Next: python manage.py check ; reload Home and open the Overdue Invoices modal.")


if __name__ == "__main__":
    main()