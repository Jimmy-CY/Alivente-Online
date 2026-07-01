"""
Apply: single source of truth for a monthly invoice's amount.

Introduces invoices.effective_amount (invoice_amount override, else tenant
base rent) and repoints every read at it, so the Open Invoices list and the
Debtors Age Analysis report can no longer disagree.

Edits, all fail-loud (each anchor must appear exactly once or NOTHING is
written to ANY file):

  pages/models.py
    + effective_amount @property on the invoices model.

  pages/views/invoices.py
    ~ invoices_page queryset gains .select_related('tenant') so the property
      does not N+1 over the unpaid list.
    ~ open_invoices_report: the two inline `invoice_amount = ...; if None:`
      coalesce blocks collapse onto invoice_obj.effective_amount
      (behaviourally identical -- invoice_obj.tenant IS tenant_obj there,
      and unpaid_invoices already select_related's 'tenant').

  pages/templates/invoices.html
    ~ Amount cell reads iresults.effective_amount instead of the always-base
      tresults.tenant_rent. The surrounding Euro sign is outside the anchor
      and untouched.

No migration is required (a property is not a DB field); makemigrations will
report "No changes detected".

Run from the repo root:  python apply_effective_amount.py
"""
import ast
import os
import sys


# --------------------------------------------------------------------------
# Edit definitions
# --------------------------------------------------------------------------

OLD_MODEL = '''    class Meta:
        db_table="invoice"'''
NEW_MODEL = '''    class Meta:
        db_table="invoice"

    @property
    def effective_amount(self):
        """Amount to bill/collect for this invoice.

        Returns the per-invoice override (invoice_amount) when set -- what the
        physical-invoice send cron writes for flagged tenants -- and falls back
        to the tenant's base rent otherwise. Single source of truth for the
        Open Invoices list and the Debtors Age Analysis report so the two
        can no longer drift.
        """
        if self.invoice_amount is not None:
            return self.invoice_amount
        return self.tenant.tenant_rent or 0'''

OLD_QS = '''    iresults = invoices.objects.filter(invoice_paid="No").order_by('invoice_date')'''
NEW_QS = '''    iresults = invoices.objects.filter(invoice_paid="No").select_related('tenant').order_by('invoice_date')'''

OLD_REP1 = '''            invoice_amount = invoice_obj.invoice_amount
            if invoice_amount is None:
                invoice_amount = tenant_obj.tenant_rent or 0

            tenant_invoices.append({'''
NEW_REP1 = '''            invoice_amount = invoice_obj.effective_amount

            tenant_invoices.append({'''

OLD_REP2 = '''            invoice_amount = invoice_obj.invoice_amount
            if invoice_amount is None:
                invoice_amount = tenant_obj.tenant_rent or 0
            amount = float(invoice_amount)'''
NEW_REP2 = '''            amount = float(invoice_obj.effective_amount)'''

OLD_TPL = '{{ tresults.tenant_rent|floatformat:0 }}'
NEW_TPL = '{{ iresults.effective_amount|floatformat:0 }}'

MODELS = os.path.join("pages", "models.py")
VIEWS = os.path.join("pages", "views", "invoices.py")
TPL = os.path.join("pages", "templates", "invoices.html")

PLAN = {
    MODELS: [(OLD_MODEL, NEW_MODEL)],
    VIEWS: [(OLD_QS, NEW_QS), (OLD_REP1, NEW_REP1), (OLD_REP2, NEW_REP2)],
    TPL: [(OLD_TPL, NEW_TPL)],
}
PY_FILES = {MODELS, VIEWS}


def main():
    # --- read + validate every anchor before touching anything ------------
    problems = []
    srcs = {}
    for path, edits in PLAN.items():
        if not os.path.isfile(path):
            problems.append(f"{path}: not found (run from repo root).")
            continue
        with open(path, "r", encoding="utf-8", newline="") as fh:
            s = fh.read()
        srcs[path] = s
        for old, new in edits:
            c = s.count(old)
            if c != 1:
                problems.append(f"{path}: anchor found {c}x (expected 1): {old[:60]!r}")
            if new in s:
                problems.append(f"{path}: replacement already present: {new[:60]!r}")

    if problems:
        print("ABORT -- nothing written:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    # --- apply per file, backup, ast-check python -------------------------
    for path, edits in PLAN.items():
        s = srcs[path]
        for old, new in edits:
            s = s.replace(old, new)

        if path in PY_FILES:
            try:
                ast.parse(s)
            except SyntaxError as e:
                sys.exit(f"ABORT: edited {path} fails to parse ({e}); no file changed.")

        with open(path + ".prebak", "w", encoding="utf-8", newline="") as fh:
            fh.write(srcs[path])
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(s)
        print(f"OK  {path}   ({len(edits)} edit{'s' if len(edits) != 1 else ''})   backup: {path}.prebak")

    print("\nDone. Next:")
    print("  python manage.py makemigrations    # expect: No changes detected")
    print("  python manage.py check")
    print("  restart the Django process, then reload Open Invoices")


if __name__ == "__main__":
    main()