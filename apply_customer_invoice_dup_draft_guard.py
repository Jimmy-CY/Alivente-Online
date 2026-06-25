# -*- coding: utf-8 -*-
"""
Apply: two tidy-ups to the customer-invoice action row.

  pages/templates/customer_invoice_form.html
    1. Hide the edit-screen Duplicate button on DRAFT invoices. A draft is the
       editable state (Save + Approve); Duplicate belongs only on approved/sent
       invoices, where it is the re-issue path. (The list row keeps Duplicate on
       every customer invoice.)
    2. Space the action-row buttons so Duplicate / Send / Un-approve don't touch.

Single-file, surgical. No view/route/migration changes.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_customer_invoice_dup_draft_guard.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "customer_invoice_form.html")

EDITS = [
    # 1) guard the Duplicate form: only when not a draft
    ('''  <div class="status-action-row">
    <form method="post" action="{% url 'customer_invoice_duplicate' pi.pk %}" class="status-action-form"
          onsubmit="return confirm('Create a new draft copy of this invoice, dated today?');">
      {% csrf_token %}
      <button type="submit" class="btn btn-duplicate">
        <i class="fas fa-copy"></i> Duplicate
      </button>
    </form>''',
     '''  <div class="status-action-row">
    {% if pi.status != 'draft' %}
    <form method="post" action="{% url 'customer_invoice_duplicate' pi.pk %}" class="status-action-form"
          onsubmit="return confirm('Create a new draft copy of this invoice, dated today?');">
      {% csrf_token %}
      <button type="submit" class="btn btn-duplicate">
        <i class="fas fa-copy"></i> Duplicate
      </button>
    </form>
    {% endif %}'''),

    # 2) gap between action-row buttons
    (".status-action-row { display: flex; justify-content: flex-end; margin-top: 20px; }",
     ".status-action-row { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; flex-wrap: wrap; }"),
]


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
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

    with io.open(TPL + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (TPL, TPL))
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()