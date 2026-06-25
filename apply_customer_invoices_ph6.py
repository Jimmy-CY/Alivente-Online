# -*- coding: utf-8 -*-
"""
Apply: Phase 6 — Physical Invoices list integration (tenant + customer).

  pages/views/physical_invoices.py  (physical_invoice_list)
    ~ query: select_related customer too; add ?type= filter (tenant/customer/all);
      order by display name across both kinds (fixes the 500 on null tenant)
    ~ row-builder: resolve name/property/kind/is_customer per invoice type
    ~ context: pass inv_type through

  pages/templates/physical_invoice_list.html
    + a Type filter (All / Tenant / Customer) beside Status
    + a Type column (header + per-row badge)
    ~ Number link routes to customer_invoice_edit for customer rows
    ~ empty-row colspan 6 -> 7
    + filter grid becomes 3 columns; auto-submit includes the Type select

First effect: the list no longer 500s on a month containing customer invoices.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_customer_invoices_ph6.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
TPL = os.path.join("pages", "templates", "physical_invoice_list.html")

# ---------------------------------------------------------------- views.py
V_Q_OLD = '''    status = (request.GET.get("status") or "").strip()
    qs = base.select_related("tenant", "tenant__prop").order_by("tenant__tenant_name")
    if status in (PhysicalInvoice.STATUS_DRAFT, PhysicalInvoice.STATUS_APPROVED,
                  PhysicalInvoice.STATUS_SENT):
        qs = qs.filter(status=status)'''
V_Q_NEW = '''    status = (request.GET.get("status") or "").strip()
    inv_type = (request.GET.get("type") or "").strip()  # "tenant" | "customer" | "" (all)
    qs = base.select_related("tenant", "tenant__prop", "customer")
    if status in (PhysicalInvoice.STATUS_DRAFT, PhysicalInvoice.STATUS_APPROVED,
                  PhysicalInvoice.STATUS_SENT):
        qs = qs.filter(status=status)
    if inv_type == "tenant":
        qs = qs.filter(tenant__isnull=False)
    elif inv_type == "customer":
        qs = qs.filter(tenant__isnull=True)
    # Order by display name across both kinds (tenant name or customer snapshot name).
    qs = sorted(
        qs,
        key=lambda pi: (pi.tenant.tenant_name if pi.tenant_id else (pi.bill_name or "")).lower())'''

V_R_OLD = '''    rows = []
    for pi in qs:
        rows.append({
            "pk": pi.pk,
            "number": pi.invoice_number or provisional.get(pi.pk, "\\u2014"),
            "tenant": pi.tenant.tenant_name,
            "property": getattr(pi.tenant.prop, "prop_name", "") or "",
            "total_display": _money(pi.total),
            "currency": pi.currency or "EUR",
            "status": pi.status,
            "status_display": pi.get_status_display(),
            "is_editable": pi.is_editable,
        })'''
V_R_NEW = '''    rows = []
    for pi in qs:
        is_customer = pi.tenant_id is None
        if is_customer:
            who = pi.bill_name or "(unnamed customer)"
            prop_name = "\\u2014"
        else:
            who = pi.tenant.tenant_name
            prop_name = getattr(pi.tenant.prop, "prop_name", "") or ""
        rows.append({
            "pk": pi.pk,
            "number": pi.invoice_number or provisional.get(pi.pk, "\\u2014"),
            "tenant": who,
            "property": prop_name,
            "kind": "Customer" if is_customer else "Tenant",
            "is_customer": is_customer,
            "total_display": _money(pi.total),
            "currency": pi.currency or "EUR",
            "status": pi.status,
            "status_display": pi.get_status_display(),
            "is_editable": pi.is_editable,
        })'''

V_C_OLD = '''        "status": status,
        "next_number_value": cfg.next_number,'''
V_C_NEW = '''        "status": status,
        "inv_type": inv_type,
        "next_number_value": cfg.next_number,'''

# ---------------------------------------------------------------- template
T_FILTER_OLD = '''          <div class="filter-group">
            <label class="filter-label"><i class="fas fa-info-circle"></i> Status</label>
            <select name="status" class="form-control filter-select" id="statusSelect">
              <option value="">All Statuses</option>
              <option value="draft" {% if status == 'draft' %}selected{% endif %}>Draft</option>
              <option value="approved" {% if status == 'approved' %}selected{% endif %}>Approved</option>
              <option value="sent" {% if status == 'sent' %}selected{% endif %}>Sent</option>
            </select>
          </div>'''
T_FILTER_NEW = T_FILTER_OLD + '''
          <div class="filter-group">
            <label class="filter-label"><i class="fas fa-tags"></i> Type</label>
            <select name="type" class="form-control filter-select" id="typeSelect">
              <option value="">All Types</option>
              <option value="tenant" {% if inv_type == 'tenant' %}selected{% endif %}>Tenant</option>
              <option value="customer" {% if inv_type == 'customer' %}selected{% endif %}>Customer</option>
            </select>
          </div>'''

T_THEAD_OLD = '''        <tr>
          <th style="width: 14%">Number</th>
          <th style="text-align: left; width: 30%">Tenant</th>
          <th style="width: 16%">Property</th>
          <th style="width: 14%">Total</th>
          <th style="width: 10%">Status</th>
          <th style="width: 16%">Actions</th>
        </tr>'''
T_THEAD_NEW = '''        <tr>
          <th style="width: 12%">Number</th>
          <th style="text-align: left; width: 26%">Name</th>
          <th style="width: 9%">Type</th>
          <th style="width: 15%">Property</th>
          <th style="width: 13%">Total</th>
          <th style="width: 10%">Status</th>
          <th style="width: 15%">Actions</th>
        </tr>'''

T_CELLS_OLD = '''            <td data-label="Number" class="pi-number">
              <a href="{% url 'physical_invoice_edit' row.pk %}" class="pi-number-link">{{ row.number }}</a>
            </td>
            <td data-label="Tenant" style="text-align: left">{{ row.tenant }}</td>
            <td data-label="Property">{{ row.property }}</td>'''
T_CELLS_NEW = '''            <td data-label="Number" class="pi-number">
              {% if row.is_customer %}
                <a href="{% url 'customer_invoice_edit' row.pk %}" class="pi-number-link">{{ row.number }}</a>
              {% else %}
                <a href="{% url 'physical_invoice_edit' row.pk %}" class="pi-number-link">{{ row.number }}</a>
              {% endif %}
            </td>
            <td data-label="Name" style="text-align: left">{{ row.tenant }}</td>
            <td data-label="Type">
              <span class="type-badge type-{% if row.is_customer %}customer{% else %}tenant{% endif %}">{{ row.kind }}</span>
            </td>
            <td data-label="Property">{{ row.property }}</td>'''

T_COLSPAN_OLD = '''            <td colspan="6" class="pi-empty">'''
T_COLSPAN_NEW = '''            <td colspan="7" class="pi-empty">'''

T_GRIDCSS_OLD = ".filter-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: end; }"
T_GRIDCSS_NEW = (".filter-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; align-items: end; }\n"
                 ".type-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }\n"
                 ".type-tenant { background: #e2e3f3; color: #3b3f8f; }\n"
                 ".type-customer { background: #d1ecf1; color: #0c5460; }")

T_JS_OLD = "['periodInput', 'statusSelect'].forEach(function (id) {"
T_JS_NEW = "['periodInput', 'statusSelect', 'typeSelect'].forEach(function (id) {"


def _load(path):
    if not os.path.exists(path):
        return None
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def main():
    targets = {
        VIEWS: [(V_Q_OLD, V_Q_NEW), (V_R_OLD, V_R_NEW), (V_C_OLD, V_C_NEW)],
        TPL: [(T_FILTER_OLD, T_FILTER_NEW), (T_THEAD_OLD, T_THEAD_NEW),
              (T_CELLS_OLD, T_CELLS_NEW), (T_COLSPAN_OLD, T_COLSPAN_NEW),
              (T_GRIDCSS_OLD, T_GRIDCSS_NEW), (T_JS_OLD, T_JS_NEW)],
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
    print("then open the Physical Invoices list and filter to June 2026.")


if __name__ == "__main__":
    main()