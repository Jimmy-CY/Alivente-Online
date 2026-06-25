# -*- coding: utf-8 -*-
"""
Apply: Phase 4 — Duplicate a customer (non-tenant) invoice.

  pages/views/physical_invoices.py
    + "customer_invoice_duplicate" in __all__
    + customer_invoice_duplicate() view: clones bill_* snapshot + customer link
      + vat_rate + all lines into a FRESH DRAFT; resets date->today (period
      re-derives), clears the number; lands on the new draft's edit screen.

  pages/urls.py
    + invoice-customers/invoice/<id>/duplicate/ -> customer_invoice_duplicate

  pages/templates/physical_invoice_list.html
    + Duplicate button on the row Actions (desktop + mobile), customer rows
    + .icon-duplicate / .icon-color-duplicate styles

  pages/templates/customer_invoice_form.html
    + Duplicate button in the action row (always available on a customer invoice,
      including a locked SENT one — it is how you re-issue)
    + .btn-duplicate style

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_customer_invoices_ph4_duplicate.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
URLS = os.path.join("pages", "urls.py")
LIST_TPL = os.path.join("pages", "templates", "physical_invoice_list.html")
FORM_TPL = os.path.join("pages", "templates", "customer_invoice_form.html")

# ----------------------------------------------------------------- views.py
V_ALL_OLD = '    "customer_invoice_send",\n]'
V_ALL_NEW = '    "customer_invoice_send",\n    "customer_invoice_duplicate",\n]'

V_APPEND_ANCHOR = '''        f"Invoice {pi.invoice_number} sent to {to_list[0]}"
        + (f" (+{len(extra_recipients)} more)" if extra_recipients else "") + ".")
    return _back()'''

V_NEW = '''


# ------------------------------------------------------------------ #
# Customer invoice: Duplicate (clone into a fresh draft)
# ------------------------------------------------------------------ #
@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def customer_invoice_duplicate(request, physical_invoice_id):
    """Clone a customer (non-tenant) invoice into a fresh DRAFT: copies the
    bill_* snapshot, the customer link, the VAT rate and all line rows; resets
    the date to today (period re-derives), clears the number, and starts in
    draft. Lands on the new draft's edit screen."""
    src = get_object_or_404(
        PhysicalInvoice.objects.prefetch_related("lines"), pk=physical_invoice_id)

    if src.tenant_id is not None:
        messages.error(request, "Duplicate is only for customer invoices.")
        return redirect("physical_invoice_list")

    today = date.today()
    with transaction.atomic():
        new_pi = PhysicalInvoice.objects.create(
            tenant=None,
            customer=src.customer,
            period_year=today.year,
            period_month=today.month,
            invoice_date=today,
            invoice_number=None,
            status=PhysicalInvoice.STATUS_DRAFT,
            vat_rate=src.vat_rate,
            currency=src.currency or "EUR",
            bill_name=src.bill_name,
            bill_customer_label=src.bill_customer_label,
            bill_address=src.bill_address,
            bill_tel=src.bill_tel,
            bill_email_to=src.bill_email_to,
            bill_email_cc=src.bill_email_cc,
            bill_email_body=src.bill_email_body,
        )
        for ln in src.lines.all():
            PhysicalInvoiceLine.objects.create(
                physical_invoice=new_pi,
                service=ln.service,
                unit_of_measure=ln.unit_of_measure,
                description=ln.description,
                qty=ln.qty,
                unit_price=ln.unit_price,
                vatable=ln.vatable,
                sort_order=ln.sort_order,
            )
        new_pi.recalc_totals()

    messages.success(
        request,
        f"Created a new draft from {src.invoice_number or 'the previous invoice'} "
        f"for {new_pi.bill_name or 'this customer'}. Adjust and finalise below.")
    return redirect("customer_invoice_edit", physical_invoice_id=new_pi.pk)'''

# ----------------------------------------------------------------- urls.py
U_OLD = '    path("invoice-customers/invoice/<int:physical_invoice_id>/send/", views.customer_invoice_send, name="customer_invoice_send"),'
U_NEW = (U_OLD + '\n'
         '    path("invoice-customers/invoice/<int:physical_invoice_id>/duplicate/", views.customer_invoice_duplicate, name="customer_invoice_duplicate"),')

# ----------------------------------------------- list template: desktop duplicate button
# Insert before the desktop PDF link (now preceded by the Send block from 5b; anchor on the
# PDF link itself, which is unique by its icon-view class).
LT_DESK_OLD = '''              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="icon-action-btn icon-view" title="View invoice PDF">
                <i class="fas fa-file-pdf"></i>
              </a>'''
LT_DESK_NEW = '''              {% if perms.auth.can_edit_tenants and row.is_customer %}
                <form method="post" action="{% url 'customer_invoice_duplicate' row.pk %}" class="pi-inline-form"
                      onsubmit="return confirm('Create a new draft copy of this invoice, dated today?');">
                  {% csrf_token %}
                  <button type="submit" class="icon-action-btn icon-duplicate" title="Duplicate as new draft">
                    <i class="fas fa-copy"></i>
                  </button>
                </form>
              {% endif %}
              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="icon-action-btn icon-view" title="View invoice PDF">
                <i class="fas fa-file-pdf"></i>
              </a>'''

# ----------------------------------------------- list template: mobile duplicate button
LT_MOB_OLD = '''              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="mobile-action-btn">
                <i class="fas fa-file-pdf mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View PDF</span>
              </a>'''
LT_MOB_NEW = '''              {% if perms.auth.can_edit_tenants and row.is_customer %}
                <form method="post" action="{% url 'customer_invoice_duplicate' row.pk %}" class="pi-inline-form-mobile"
                      onsubmit="return confirm('Create a new draft copy of this invoice, dated today?');">
                  {% csrf_token %}
                  <button type="submit" class="mobile-action-btn">
                    <i class="fas fa-copy mobile-action-icon icon-color-duplicate"></i>
                    <span class="mobile-action-label">Duplicate</span>
                  </button>
                </form>
              {% endif %}
              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="mobile-action-btn">
                <i class="fas fa-file-pdf mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View PDF</span>
              </a>'''

# ----------------------------------------------- list template: desktop icon CSS
LT_CSS_OLD = ".icon-send { color: #007bff; border-color: #007bff; }\n.icon-send:hover { background-color: #007bff; color: white; }"
LT_CSS_NEW = (".icon-send { color: #007bff; border-color: #007bff; }\n"
              ".icon-send:hover { background-color: #007bff; color: white; }\n"
              ".icon-duplicate { color: #6f42c1; border-color: #6f42c1; }\n"
              ".icon-duplicate:hover { background-color: #6f42c1; color: white; }")

# ----------------------------------------------- list template: mobile colour CSS
LT_MCSS_OLD = "  .icon-color-send { color: #007bff; }"
LT_MCSS_NEW = "  .icon-color-send { color: #007bff; }\n  .icon-color-duplicate { color: #6f42c1; }"

# --------------------------------------------- form template: edit-screen duplicate button
# Place a Duplicate form at the start of the action row so it is available in EVERY status,
# including a locked sent invoice. Anchor on the action-row opening (unique).
FT_OLD = '''{% if mode == 'edit' and perms.auth.can_edit_tenants %}
  <div class="status-action-row">'''
FT_NEW = '''{% if mode == 'edit' and perms.auth.can_edit_tenants %}
  <div class="status-action-row">
    <form method="post" action="{% url 'customer_invoice_duplicate' pi.pk %}" class="status-action-form"
          onsubmit="return confirm('Create a new draft copy of this invoice, dated today?');">
      {% csrf_token %}
      <button type="submit" class="btn btn-duplicate">
        <i class="fas fa-copy"></i> Duplicate
      </button>
    </form>'''

# ----------------------------------------------- form template: btn-duplicate CSS
FT_CSS_OLD = ".btn-send:hover { background-color: #0069d9; border-color: #0062cc; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }"
FT_CSS_NEW = (".btn-send:hover { background-color: #0069d9; border-color: #0062cc; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }\n"
              ".btn-duplicate { background-color: #6f42c1; color: white; border: 1px solid #6f42c1; border-radius: 6px; font-weight: 500; padding: 8px 18px; transition: all 0.2s ease; }\n"
              ".btn-duplicate:hover { background-color: #5e37a6; border-color: #563098; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }")


def _load(path):
    if not os.path.exists(path):
        return None
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def main():
    targets = {
        VIEWS: [(V_ALL_OLD, V_ALL_NEW), (V_APPEND_ANCHOR, V_APPEND_ANCHOR + V_NEW)],
        URLS: [(U_OLD, U_NEW)],
        LIST_TPL: [(LT_DESK_OLD, LT_DESK_NEW), (LT_MOB_OLD, LT_MOB_NEW),
                   (LT_CSS_OLD, LT_CSS_NEW), (LT_MCSS_OLD, LT_MCSS_NEW)],
        FORM_TPL: [(FT_OLD, FT_NEW), (FT_CSS_OLD, FT_CSS_NEW)],
    }

    srcs, problems = {}, []
    for path, edits in targets.items():
        src = _load(path)
        if src is None:
            problems.append("  MISSING FILE: %s" % path)
            continue
        srcs[path] = src
        for i, (old, _new) in enumerate(edits, 1):
            n = src.count(old)
            if n != 1:
                problems.append("  %s edit %d: anchor found %d time(s) (expected 1)" % (path, i, n))
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    results = []
    for path, edits in targets.items():
        new_src = srcs[path]
        for old, new in edits:
            new_src = new_src.replace(old, new, 1)
        if path.endswith(".py"):
            try:
                ast.parse(new_src)
            except SyntaxError as e:
                sys.exit("ABORTED - %s does not parse: %s" % (path, e))
        results.append((path, srcs[path], new_src))

    for path, src, new_src in results:
        with io.open(path + ".prebak", "w", encoding="utf-8", newline="") as fh:
            fh.write(src)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_src)
        print("OK: %s (backup %s.prebak)" % (path, path))

    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()