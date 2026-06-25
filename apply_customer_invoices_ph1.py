# -*- coding: utf-8 -*-
"""
Apply: Phase 1 of customer (non-tenant) invoices — schema only.

  pages/models.py
    + new InvoiceCustomer model (inserted before PhysicalInvoiceProfile)
    ~ PhysicalInvoice.tenant -> null=True, blank=True (stays PROTECT)
    + PhysicalInvoice.customer FK (PROTECT) + 7 bill_* snapshot fields
    ~ physical_invoice_pdf_upload_path(): tenant-name fallback to bill_name
    ~ PhysicalInvoice.__str__(): tenant fallback to bill_name

The matching migration pages/migrations/0084_... is delivered separately and
must be copied into pages/migrations/ before migrating.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:
    python manage.py makemigrations --check --dry-run   (expect: no changes)
    python manage.py check
    python manage.py migrate

Run from the repo root:  python apply_customer_invoices_ph1.py
"""
import ast
import io
import os
import sys

MODELS = os.path.join("pages", "models.py")

TENANT_OLD = "    tenant = models.ForeignKey(tenant, on_delete=models.PROTECT, related_name='physical_invoices')"
TENANT_NEW = (
    "    tenant = models.ForeignKey(tenant, on_delete=models.PROTECT, null=True, blank=True,\n"
    "                               related_name='physical_invoices')\n"
    "    # Customer (non-tenant) invoices: tenant is NULL, customer + bill_* snapshot are used.\n"
    "    customer = models.ForeignKey('InvoiceCustomer', on_delete=models.PROTECT,\n"
    "                                 null=True, blank=True, related_name='invoices')\n"
    "    bill_name = models.CharField(max_length=255, blank=True)\n"
    "    bill_customer_label = models.CharField(max_length=255, blank=True)\n"
    "    bill_address = models.TextField(blank=True)\n"
    "    bill_tel = models.CharField(max_length=64, blank=True)\n"
    "    bill_email_to = models.TextField(blank=True,\n"
    "        help_text='Comma-separated To addresses for a customer invoice.')\n"
    "    bill_email_cc = models.TextField(blank=True,\n"
    "        help_text='Comma-separated CC addresses for a customer invoice.')\n"
    "    bill_email_body = models.TextField(blank=True)"
)

PATH_OLD = "    tenant_slug = slugify(getattr(instance.tenant, 'tenant_name', '') or 'tenant')"
PATH_NEW = (
    "    if getattr(instance, 'tenant_id', None):\n"
    "        name = getattr(instance.tenant, 'tenant_name', '') or 'tenant'\n"
    "    else:\n"
    "        name = getattr(instance, 'bill_name', '') or 'customer'\n"
    "    tenant_slug = slugify(name)"
)

STR_OLD = '        return f"{self.invoice_number or \'DRAFT\'} — {self.tenant} — {self.period_month:02d}/{self.period_year}"'
STR_NEW = (
    "        who = self.tenant if self.tenant_id else (self.bill_name or 'Customer')\n"
    '        return f"{self.invoice_number or \'DRAFT\'} — {who} — {self.period_month:02d}/{self.period_year}"'
)

CUST_ANCHOR = "class PhysicalInvoiceProfile(models.Model):"
CUST_NEW = '''class InvoiceCustomer(models.Model):
    """A non-tenant customer for ad-hoc (customer) invoices. The invoice freezes
    its own copy of these fields (bill_*), so editing or deleting a customer
    never rewrites an already-issued invoice. PROTECT on the invoice FK means a
    customer with invoices cannot be deleted."""
    name = models.CharField(max_length=255)
    customer_id_label = models.CharField(max_length=255, blank=True,
        help_text="Shown in the 'Customer ID' box on the invoice.")
    billing_address = models.TextField(blank=True, help_text="One line per row.")
    billing_tel = models.CharField(max_length=64, blank=True)
    email_to = models.TextField(blank=True, help_text="Comma-separated To addresses.")
    email_cc = models.TextField(blank=True, help_text="Comma-separated CC addresses.")
    email_body = models.TextField(blank=True,
        help_text="Optional saved greeting/body for this customer's invoice e-mail. "
                  "Blank uses a generic default.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoice_customers"
        verbose_name = "Invoice Customer"
        verbose_name_plural = "Invoice Customers"
        ordering = ["name"]

    def __str__(self):
        return self.name


'''

EDITS = [
    (TENANT_OLD, TENANT_NEW),
    (PATH_OLD, PATH_NEW),
    (STR_OLD, STR_NEW),
    (CUST_ANCHOR, CUST_NEW + CUST_ANCHOR),
]


def main():
    if not os.path.exists(MODELS):
        sys.exit("ABORTED - missing file: %s" % MODELS)
    with io.open(MODELS, "r", encoding="utf-8") as fh:
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
        sys.exit("ABORTED - %s does not parse: %s" % (MODELS, e))

    with io.open(MODELS + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(MODELS, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (MODELS, MODELS))
    print("done. copy 0084 into pages/migrations/, then:")
    print("  python manage.py makemigrations --check --dry-run")
    print("  python manage.py check")
    print("  python manage.py migrate")


if __name__ == "__main__":
    main()