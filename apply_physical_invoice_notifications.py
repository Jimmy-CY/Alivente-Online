"""
Apply: two notification cards for the physical invoice feature.

  pages/models.py
    1. add ('physical_invoice_client', 'Physical Invoice to Client') to
       NotificationRecipient.NOTIFICATION_TYPES

  pages/views/notifications.py
    2. add both physical-invoice types to admin_types so the settings page
       populates them

  pages/templates/notification_settings.html
    3. insert the two cards (draft reminders = TO/CC; client invoice = CC-only,
       TO comes from the tenant record) before the Expense Needs Approval card

Fail-loud: every anchor must appear exactly once across all files or nothing
is written. After running: makemigrations pages (choices change), migrate, check.

Run from the repo root:  python apply_physical_invoice_notifications.py
"""
import ast
import io
import os
import sys

MODELS = os.path.join("pages", "models.py")
VIEW = os.path.join("pages", "views", "notifications.py")
TPL = os.path.join("pages", "templates", "notification_settings.html")

MODELS_EDITS = [
    ("""        ('physical_invoice_review', 'Physical Invoices Awaiting Approval'),
    )""",
     """        ('physical_invoice_review', 'Physical Invoices Awaiting Approval'),
        ('physical_invoice_client', 'Physical Invoice to Client'),
    )"""),
]

VIEW_EDITS = [
    ("""        'invoice_paid',
        'expense_needs_approval',""",
     """        'invoice_paid',
        'physical_invoice_review',
        'physical_invoice_client',
        'expense_needs_approval',"""),
]

CARD_REVIEW = """<!-- Physical Invoices Awaiting Approval -->
<div class="notification-card">
    <h5><i class="fas fa-file-invoice-dollar"></i> Physical Invoices Awaiting Approval</h5>
    <p class="text-muted">Daily reminder listing the physical invoice drafts that still need approving before the 1st. Sent only while drafts are pending.</p>

    <form method="post">
        {% csrf_token %}
        <input type="hidden" name="notification_type" value="physical_invoice_review">

        <div class="form-group">
            <label><strong>TO:</strong> Primary Recipients</label>
            <textarea
                class="form-control"
                name="to_addresses"
                rows="2"
                placeholder="email1@example.com, email2@example.com"
            >{{ notification_settings.physical_invoice_review.to_emails }}</textarea>
            <div class="field-hint">People who approve the physical invoice drafts</div>
        </div>

        <div class="form-group">
            <label><strong>CC:</strong> Carbon Copy Recipients (optional)</label>
            <textarea
                class="form-control"
                name="cc_addresses"
                rows="2"
                placeholder="email1@example.com, email2@example.com"
            >{{ notification_settings.physical_invoice_review.cc_emails }}</textarea>
            <div class="field-hint">Additional recipients who should be informed</div>
        </div>

        <button type="submit" class="btn btn-info">
            <i class="fas fa-save"></i> Save
        </button>
    </form>
</div>

<!-- Physical Invoice to Client -->
<div class="notification-card">
    <h5><i class="fas fa-paper-plane"></i> Physical Invoice to Client</h5>
    <p class="text-muted">The monthly physical invoice PDF emailed to each tenant on the 1st. The recipient is the tenant's own email from their record; set any addresses to copy on every client invoice below.</p>

    <form method="post">
        {% csrf_token %}
        <input type="hidden" name="notification_type" value="physical_invoice_client">

        <div class="form-group">
            <label><strong>TO:</strong> Primary Recipient</label>
            <div class="field-hint" style="font-style: normal; margin-top: 0;">
                <i class="fas fa-info-circle"></i> Sent automatically to each tenant's email address (from the tenant record). Not configurable here.
            </div>
        </div>

        <div class="form-group">
            <label><strong>CC:</strong> Carbon Copy Recipients (optional)</label>
            <textarea
                class="form-control"
                name="cc_addresses"
                rows="2"
                placeholder="email1@example.com, email2@example.com"
            >{{ notification_settings.physical_invoice_client.cc_emails }}</textarea>
            <div class="field-hint">Copied on every client invoice (e.g. your accounts mailbox)</div>
        </div>

        <button type="submit" class="btn btn-info">
            <i class="fas fa-save"></i> Save
        </button>
    </form>
</div>

<!-- Expense Needs Approval -->"""

TPL_EDITS = [
    ("""<!-- Expense Needs Approval -->""", CARD_REVIEW),
]


def _verify(path, edits):
    if not os.path.exists(path):
        return None, ["MISSING FILE: %s" % path]
    with io.open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    problems = []
    for i, (old, _new) in enumerate(edits, 1):
        n = src.count(old)
        if n != 1:
            problems.append("  %s edit %d: anchor found %d time(s) (expected 1)" % (path, i, n))
    return src, problems


def main():
    targets = [(MODELS, MODELS_EDITS, True), (VIEW, VIEW_EDITS, True), (TPL, TPL_EDITS, False)]

    loaded, all_problems = [], []
    for path, edits, is_py in targets:
        src, problems = _verify(path, edits)
        all_problems.extend(problems)
        loaded.append((path, edits, is_py, src))
    if all_problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(all_problems))

    results = []
    for path, edits, is_py, src in loaded:
        new_src = src
        for old, new in edits:
            new_src = new_src.replace(old, new, 1)
        if is_py:
            try:
                ast.parse(new_src)
            except SyntaxError as e:
                sys.exit("ABORTED - %s does not parse: %s" % (path, e))
        results.append((path, src, new_src))

    for path, src, new_src in results:
        with io.open(path + ".prebak", "w", encoding="utf-8", newline="") as fh:
            fh.write(src)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_src)
        print("OK: %s (backup %s.prebak)" % (path, path))

    print("done. next: makemigrations pages, migrate, check")


if __name__ == "__main__":
    main()