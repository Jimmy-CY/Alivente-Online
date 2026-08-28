"""Cash-receipt (CR) number assignment.

One running counter (CashReceiptNumbering). The suggested next number is the
counter, reconciled against the highest number already issued so the sequence
can never go backwards.

WHY BOTH. The counter alone can be wrong - restored from a backup, edited by
hand, or advanced by a transaction that later rolled back. The highest issued
alone cannot survive the whole book being voided, and reading every row to
issue one receipt is the wrong shape. `max(counter, highest + 1)` is right
whichever of the two has drifted.

A VOIDED RECEIPT STILL COUNTS. `highest_issued_number` deliberately does not
filter out voided rows: a voided number has been used and must never be
handed out again. That is the whole reason voiding is not deleting.

Deliberately a separate counter from the invoice one. Receipts and invoices
are different sequences; sharing a counter would interleave them.
"""
import re

from django.db import transaction

from pages.models import CashReceipt, CashReceiptNumbering

_TRAILING_NUM = re.compile(r"(\d+)\s*$")


def _numeric_part(receipt_number, prefix):
    if not receipt_number:
        return None
    s = receipt_number.strip()
    if prefix and s.startswith(prefix):
        s = s[len(prefix):]
    m = _TRAILING_NUM.search(s)
    return int(m.group(1)) if m else None


def highest_issued_number(settings=None):
    settings = settings or CashReceiptNumbering.get_solo()
    highest = 0
    for num in (CashReceipt.objects
                .exclude(receipt_number__isnull=True)
                .exclude(receipt_number="")
                .values_list("receipt_number", flat=True)):
        n = _numeric_part(num, settings.prefix)
        if n and n > highest:
            highest = n
    return highest


def suggested_next_number(settings=None):
    settings = settings or CashReceiptNumbering.get_solo()
    return max(settings.next_number, highest_issued_number(settings) + 1)


def preview_next(settings=None):
    """The formatted number the next receipt WOULD get. For display only.

    Never write this to a record. Two people with the issue form open would
    both be shown CR-00372; only `assign_next` decides which of them gets it.
    """
    settings = settings or CashReceiptNumbering.get_solo()
    return settings.format(suggested_next_number(settings))


def assign_next():
    """Take the next number and advance the counter, atomically.

    `select_for_update` on the singleton is what makes two simultaneous issues
    safe: the second waits for the first to commit, then reads the advanced
    counter. Without it both read 372 and the unique index on receipt_number
    rejects the loser - correct, but as a 500 rather than as a queue.

    Must be called inside a transaction, alongside the row it numbers, so a
    failure to save the receipt cannot leave the counter advanced past a
    number nothing ever used.
    """
    settings = (CashReceiptNumbering.objects.select_for_update().first()
                or CashReceiptNumbering.objects.create())
    n = suggested_next_number(settings)
    number = settings.format(n)
    settings.next_number = n + 1
    settings.save(update_fields=["next_number", "updated_at"])
    return number
