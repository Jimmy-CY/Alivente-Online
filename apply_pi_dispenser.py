# -*- coding: utf-8 -*-
"""
Apply: drop the per-invoice number box, add the "dispenser" (next-number) control.

  pages/views/physical_invoices.py
    - REVERT the manual invoice_number save in physical_invoice_edit's POST.
    + import PhysicalInvoiceNumbering
    + expose the current next-number on the list view (next_number_value/display)
    + add "physical_invoice_set_next_number" to __all__
    + append physical_invoice_set_next_number (POST, auth.can_edit_tenants):
      sets the PR-number counter.

  pages/urls.py
    + route physical-invoices/set-next-number/

  pages/templates/physical_invoice_edit.html
    - REVERT the editable Invoice Number box back to a read-only "Number".

The list template (with the dispenser control UI) is delivered separately.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_pi_dispenser.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
URLS = os.path.join("pages", "urls.py")
EDIT_TPL = os.path.join("pages", "templates", "physical_invoice_edit.html")

NEW_VIEW = '''

@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def physical_invoice_set_next_number(request):
    """Set the running PR-number counter (the 'dispenser'). Use this when
    invoices issued outside the system have consumed numbers, so the next
    auto-assigned number resumes from the right place."""
    cfg = PhysicalInvoiceNumbering.get_solo()
    raw = (request.POST.get("next_number") or "").strip()
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = 0
    if value < 1:
        messages.error(request, "Enter a whole number of 1 or more for the next invoice number.")
    else:
        cfg.next_number = value
        cfg.save(update_fields=["next_number", "updated_at"])
        messages.success(request, f"Next invoice number set to {cfg.format(cfg.next_number)}.")
    nxt = request.POST.get("next") or ""
    if nxt and url_has_allowed_host_and_scheme(
            nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)
    return redirect(reverse("physical_invoice_list"))
'''

VIEWS_EDITS = [
    # import the numbering singleton
    ("from pages.models import PhysicalInvoice, PhysicalInvoiceLine",
     "from pages.models import PhysicalInvoice, PhysicalInvoiceLine, PhysicalInvoiceNumbering"),

    # REVERT the manual invoice_number save
    ('''            pi.recalc_totals()

        # Manual invoice number override (blank = auto-assign on send).
        manual_number = (request.POST.get("invoice_number") or "").strip()[:32]
        pi.invoice_number = manual_number or None
        pi.save(update_fields=["invoice_number", "updated_at"])

        messages.success(''',
     '''            pi.recalc_totals()

        messages.success('''),

    # expose the dispenser value on the list view
    ('''    context = {
        "rows": rows,
        "counts": counts,
        "period_value": f"{y:04d}-{m:02d}",
        "period_label": period_first.strftime("%B %Y"),
        "status": status,
    }
    return render(request, "physical_invoice_list.html", context)''',
     '''    cfg = PhysicalInvoiceNumbering.get_solo()
    context = {
        "rows": rows,
        "counts": counts,
        "period_value": f"{y:04d}-{m:02d}",
        "period_label": period_first.strftime("%B %Y"),
        "status": status,
        "next_number_value": cfg.next_number,
        "next_number_display": cfg.format(cfg.next_number),
    }
    return render(request, "physical_invoice_list.html", context)'''),

    # __all__
    ('''    "physical_invoice_approve",
    "physical_invoice_unapprove",
]''',
     '''    "physical_invoice_approve",
    "physical_invoice_unapprove",
    "physical_invoice_set_next_number",
]'''),

    # append the dispenser view after physical_invoice_unapprove
    ('''    try:
        pi.unapprove()
        messages.success(request, f"Invoice for {pi.tenant.tenant_name} moved back to draft.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
    return _redirect_after_pi_action(request, pi)''',
     '''    try:
        pi.unapprove()
        messages.success(request, f"Invoice for {pi.tenant.tenant_name} moved back to draft.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
    return _redirect_after_pi_action(request, pi)''' + NEW_VIEW),
]

URLS_EDITS = [
    ('    path("physical-invoices/<int:physical_invoice_id>/unapprove/", views.physical_invoice_unapprove, name="physical_invoice_unapprove"),',
     '    path("physical-invoices/<int:physical_invoice_id>/unapprove/", views.physical_invoice_unapprove, name="physical_invoice_unapprove"),\n'
     '    path("physical-invoices/set-next-number/", views.physical_invoice_set_next_number, name="physical_invoice_set_next_number"),'),
]

EDIT_TPL_EDITS = [
    ('''      <div class="summary-item">
        <span class="summary-label">Invoice Number</span>
        {% if is_editable %}
          <input type="text" name="invoice_number" value="{{ pi.invoice_number|default_if_none:'' }}"
                 placeholder="{{ number }} (auto on send)" maxlength="32"
                 class="form-control summary-input">
          <span class="summary-hint">Blank = auto-assigned on send. Provisional: {{ number }}</span>
        {% else %}
          <span class="summary-value">{{ number }}</span>
        {% endif %}
      </div>''',
     '      <div class="summary-item"><span class="summary-label">Number</span><span class="summary-value">{{ number }}</span></div>'),
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
    targets = [(VIEWS, VIEWS_EDITS, True), (URLS, URLS_EDITS, True), (EDIT_TPL, EDIT_TPL_EDITS, False)]
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

    print("done. next: check")


if __name__ == "__main__":
    main()