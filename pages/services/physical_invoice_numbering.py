"""Physical-invoice (PR) number assignment.

One running counter (PhysicalInvoiceNumbering). The suggested next number is
the counter, reconciled against the highest number already issued so the
sequence can never go backwards. Within a month a batch cascades by tenant
name A->Z. Final numbers are committed at SEND only, so a dropped draft leaves
no gap.
"""
import re
from pages.models import PhysicalInvoice, PhysicalInvoiceNumbering

_TRAILING_NUM = re.compile(r"(\d+)\s*$")


def _numeric_part(invoice_number, prefix):
    if not invoice_number:
        return None
    s = invoice_number.strip()
    if prefix and s.startswith(prefix):
        s = s[len(prefix):]
    m = _TRAILING_NUM.search(s)
    return int(m.group(1)) if m else None


def highest_issued_number(settings=None):
    settings = settings or PhysicalInvoiceNumbering.get_solo()
    highest = 0
    for num in (PhysicalInvoice.objects
                .exclude(invoice_number__isnull=True)
                .exclude(invoice_number="")
                .values_list("invoice_number", flat=True)):
        n = _numeric_part(num, settings.prefix)
        if n and n > highest:
            highest = n
    return highest


def suggested_next_number(settings=None):
    settings = settings or PhysicalInvoiceNumbering.get_solo()
    return max(settings.next_number, highest_issued_number(settings) + 1)


def month_batch(year, month, statuses=None):
    qs = PhysicalInvoice.objects.filter(period_year=year, period_month=month)
    if statuses:
        qs = qs.filter(status__in=statuses)
    return list(qs.select_related("tenant").order_by("tenant__tenant_name", "tenant_id"))


def preview_batch_numbers(year, month, start=None, statuses=None):
    """Provisional numbers for a month's batch, without saving. {pk: 'PR-0170'}."""
    settings = PhysicalInvoiceNumbering.get_solo()
    start = start or suggested_next_number(settings)
    return {pi.pk: settings.format(start + i)
            for i, pi in enumerate(month_batch(year, month, statuses=statuses))}


def assign_and_commit_batch(year, month, start=None, statuses=("approved",)):
    """Assign FINAL contiguous numbers (A->Z) to a month's sendable invoices and
    advance the counter past the batch. Returns [(invoice, 'PR-0170'), ...]."""
    settings = PhysicalInvoiceNumbering.get_solo()
    start = start or suggested_next_number(settings)
    assigned, n = [], start
    for pi in month_batch(year, month, statuses=statuses):
        number = settings.format(n)
        pi.invoice_number = number
        pi.save(update_fields=["invoice_number", "updated_at"])
        assigned.append((pi, number))
        n += 1
    settings.next_number = n
    settings.save(update_fields=["next_number", "updated_at"])
    return assigned