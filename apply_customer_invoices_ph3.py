# -*- coding: utf-8 -*-
"""
Apply: Phase 3 of customer (non-tenant) invoices — create / edit a customer invoice.

  pages/views/physical_invoices.py
    ~ import InvalidOperation alongside Decimal
    + add "customer_invoice_create" / "customer_invoice_edit" to __all__
    + append the create/edit views and their helpers
        _apply_customer_panel  (writes bill_* snapshot, sets customer FK per rule)
        _save_customer_lines   (same line-parsing as physical_invoice_edit)
        _parse_vat_percent / _parse_invoice_date / _customer_panel_context
        customer_invoice_create / customer_invoice_edit

  pages/urls.py  (INVOICES block)
    + invoice-customers/new-invoice/                  -> customer_invoice_create
    + invoice-customers/invoice/<id>/edit/            -> customer_invoice_edit

  pages/templates/physical_invoice_list.html
    + a "New Customer Invoice" button on the action row

Template customer_invoice_form.html is delivered separately and must be copied
into pages/templates/.

Snapshot rule (audit-safe): on save the seven bill_* fields are written from the
panel; the customer FK is linked only when an existing customer is picked, or a
typed customer is saved via the checkbox. Editing fields after picking never
changes the saved customer record.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_customer_invoices_ph3.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
URLS = os.path.join("pages", "urls.py")
LIST_TPL = os.path.join("pages", "templates", "physical_invoice_list.html")

# ------------------------------------------------------------- views.py
V_IMP_OLD = "from decimal import Decimal"
V_IMP_NEW = "from decimal import Decimal, InvalidOperation"

V_ALL_OLD = '    "customer_delete",\n]'
V_ALL_NEW = ('    "customer_delete",\n'
             '    "customer_invoice_create",\n'
             '    "customer_invoice_edit",\n'
             ']')

# Append point: end of customer_delete (the final view added in Phase 2).
V_TAIL_OLD = '''    except ProtectedError:
        n = obj.invoices.count()
        messages.error(
            request,
            f"'{name}' has {n} invoice{'' if n == 1 else 's'} and can't be deleted. "
            f"Customers with invoices are kept so the invoices stay intact.")
    return redirect("customer_list")'''

V_NEW = '''


# ------------------------------------------------------------------ #
# Customer invoices: create / edit (non-tenant)
# ------------------------------------------------------------------ #
def _apply_customer_panel(request, pi):
    """Write the seven bill_* snapshot fields from the panel, set the customer FK
    per the pick / new / save rule, and optionally create a saved customer.

      - existing picked        -> snapshot + link to that customer
      - new typed, save ticked -> create InvoiceCustomer, snapshot + link
      - new typed, not ticked  -> snapshot only, link null (one-off)

    Editing fields after picking never changes the saved customer record.
    """
    picked_id = (request.POST.get("customer_id") or "").strip()
    save_new = (request.POST.get("save_customer") or "").strip() in ("1", "true", "on", "yes")

    name = (request.POST.get("bill_name") or "").strip()
    label = (request.POST.get("bill_customer_label") or "").strip()
    address = (request.POST.get("bill_address") or "").strip()
    tel = (request.POST.get("bill_tel") or "").strip()
    email_to = (request.POST.get("bill_email_to") or "").strip()
    email_cc = (request.POST.get("bill_email_cc") or "").strip()
    email_body = (request.POST.get("bill_email_body") or "").strip()

    linked = None
    if picked_id:
        linked = InvoiceCustomer.objects.filter(pk=picked_id).first()
    elif save_new and name:
        linked = InvoiceCustomer.objects.create(
            name=name[:255], customer_id_label=label[:255], billing_address=address,
            billing_tel=tel[:64], email_to=email_to, email_cc=email_cc, email_body=email_body)

    pi.customer = linked
    pi.bill_name = name[:255]
    pi.bill_customer_label = label[:255]
    pi.bill_address = address
    pi.bill_tel = tel[:64]
    pi.bill_email_to = email_to
    pi.bill_email_cc = email_cc
    pi.bill_email_body = email_body


def _save_customer_lines(request, pi):
    """Replace the line rows from the submitted parallel arrays (same parsing as
    physical_invoice_edit), then recompute totals."""
    services = request.POST.getlist("line_service")
    uoms = request.POST.getlist("line_uom")
    descriptions = request.POST.getlist("line_description")
    qtys = request.POST.getlist("line_qty")
    prices = request.POST.getlist("line_unit_price")
    vatables = request.POST.getlist("line_vatable")

    def _at(seq, i):
        return seq[i] if i < len(seq) else ""

    def _dec(raw, default):
        try:
            return Decimal(str(raw).strip() or default)
        except (ArithmeticError, ValueError, TypeError):
            return Decimal(default)

    rows = []
    count = max(len(services), len(uoms), len(descriptions),
                len(qtys), len(prices), len(vatables))
    for i in range(count):
        service = (_at(services, i) or "").strip()
        description = (_at(descriptions, i) or "").strip()
        if not service and not description:
            continue
        rows.append({
            "service": service[:50],
            "uom": (_at(uoms, i) or "").strip()[:50],
            "description": description[:255],
            "qty": _dec(_at(qtys, i), "1"),
            "unit_price": _dec(_at(prices, i), "0"),
            "vatable": str(_at(vatables, i)).strip() in ("1", "true", "True", "yes", "Yes", "on"),
        })

    with transaction.atomic():
        pi.lines.all().delete()
        for idx, r in enumerate(rows):
            PhysicalInvoiceLine.objects.create(
                physical_invoice=pi, service=r["service"], unit_of_measure=r["uom"],
                description=r["description"], qty=r["qty"], unit_price=r["unit_price"],
                vatable=r["vatable"], sort_order=idx)
        pi.recalc_totals()


def _parse_vat_percent(raw, default=Decimal("0.19")):
    """'19' -> Decimal('0.1900'); blank/invalid -> default. Clamped 0..100%."""
    raw = (raw or "").strip()
    if not raw:
        return default
    try:
        pct = Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        return default
    if pct < 0:
        pct = Decimal("0")
    if pct > 100:
        pct = Decimal("100")
    return (pct / Decimal("100")).quantize(Decimal("0.0001"))


def _parse_invoice_date(raw):
    raw = (raw or "").strip()
    if raw:
        try:
            y, m, d = raw.split("-")
            return date(int(y), int(m), int(d))
        except (ValueError, TypeError):
            pass
    return date.today()


def _customer_panel_context(pi=None):
    return {"all_customers": InvoiceCustomer.objects.all().order_by("name")}


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def customer_invoice_create(request):
    """Create a new customer (non-tenant) invoice as a draft, then land on edit."""
    if request.method == "POST":
        inv_date = _parse_invoice_date(request.POST.get("invoice_date"))
        vat_rate = _parse_vat_percent(request.POST.get("vat_rate_percent"))
        pi = PhysicalInvoice(
            tenant=None,
            period_year=inv_date.year,
            period_month=inv_date.month,
            invoice_date=inv_date,
            status=PhysicalInvoice.STATUS_DRAFT,
            vat_rate=vat_rate,
            currency="EUR",
        )
        _apply_customer_panel(request, pi)
        if not pi.bill_name:
            messages.error(request, "A customer name is required.")
            ctx = _customer_panel_context()
            ctx.update({"mode": "create", "form_data": request.POST,
                        "invoice_date_value": inv_date.strftime("%Y-%m-%d"),
                        "vat_percent_value": (request.POST.get("vat_rate_percent") or "19"),
                        "lines": [], "is_editable": True})
            return render(request, "customer_invoice_form.html", ctx)
        pi.save()
        _save_customer_lines(request, pi)
        messages.success(request, f"Draft invoice for {pi.bill_name} created.")
        return redirect("customer_invoice_edit", physical_invoice_id=pi.pk)

    inv_date = date.today()
    ctx = _customer_panel_context()
    ctx.update({
        "mode": "create",
        "invoice_date_value": inv_date.strftime("%Y-%m-%d"),
        "vat_percent_value": "19",
        "lines": [],
        "is_editable": True,
    })
    return render(request, "customer_invoice_form.html", ctx)


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def customer_invoice_edit(request, physical_invoice_id):
    """Edit a draft customer invoice (customer panel + date + VAT + lines)."""
    pi = get_object_or_404(
        PhysicalInvoice.objects.select_related("customer"), pk=physical_invoice_id)
    if pi.tenant_id is not None:
        messages.error(request, "That is a tenant invoice; edit it from the tenant flow.")
        return redirect("physical_invoice_edit", physical_invoice_id=pi.pk)

    if request.method == "POST":
        if not pi.is_editable:
            messages.error(
                request,
                f"Invoice {pi.invoice_number or pi.pk} is {pi.get_status_display()} "
                f"and cannot be edited. Un-approve it first.")
            return redirect("customer_invoice_edit", physical_invoice_id=pi.pk)

        inv_date = _parse_invoice_date(request.POST.get("invoice_date"))
        pi.invoice_date = inv_date
        pi.period_year = inv_date.year
        pi.period_month = inv_date.month
        pi.vat_rate = _parse_vat_percent(request.POST.get("vat_rate_percent"), pi.vat_rate)
        _apply_customer_panel(request, pi)
        if not pi.bill_name:
            messages.error(request, "A customer name is required.")
            return redirect("customer_invoice_edit", physical_invoice_id=pi.pk)
        pi.save()
        _save_customer_lines(request, pi)
        messages.success(
            request,
            f"Invoice for {pi.bill_name} saved ({pi.currency} {_money(pi.total)}).")
        return redirect("customer_invoice_edit", physical_invoice_id=pi.pk)

    ctx = _customer_panel_context(pi)
    ctx.update({
        "mode": "edit",
        "pi": pi,
        "lines": pi.lines.all(),
        "invoice_date_value": (pi.invoice_date.strftime("%Y-%m-%d")
                               if pi.invoice_date else date.today().strftime("%Y-%m-%d")),
        "vat_percent_value": f"{float(pi.vat_rate) * 100:.0f}",
        "vat_rate_display": f"{float(pi.vat_rate) * 100:.2f}%",
        "number": pi.invoice_number or "(assigned at send)",
        "subtotal_display": _money(pi.subtotal),
        "vat_display": _money(pi.vat),
        "total_display": _money(pi.total),
        "is_editable": pi.is_editable,
    })
    return render(request, "customer_invoice_form.html", ctx)
'''

# ------------------------------------------------------------- urls.py
U_OLD = '    path("invoice-customers/<int:customer_id>/delete/", views.customer_delete, name="customer_delete"),'
U_NEW = (U_OLD + '\n'
         '    path("invoice-customers/new-invoice/", views.customer_invoice_create, name="customer_invoice_create"),\n'
         '    path("invoice-customers/invoice/<int:physical_invoice_id>/edit/", views.customer_invoice_edit, name="customer_invoice_edit"),')

# ------------------------------------------------------------- list template
T_OLD = '''      {% if perms.auth.can_access_tenants %}
        <a href="{% url 'customer_list' %}" class="btn btn-info action-secondary">
          <i class="fas fa-address-book"></i> Manage Customers
        </a>
      {% endif %}'''
T_NEW = '''      {% if perms.auth.can_edit_tenants %}
        <a href="{% url 'customer_invoice_create' %}" class="btn btn-info action-secondary">
          <i class="fas fa-file-invoice-dollar"></i> New Customer Invoice
        </a>
      {% endif %}
      {% if perms.auth.can_access_tenants %}
        <a href="{% url 'customer_list' %}" class="btn btn-info action-secondary">
          <i class="fas fa-address-book"></i> Manage Customers
        </a>
      {% endif %}'''


def _load(path):
    if not os.path.exists(path):
        return None
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def main():
    targets = {
        VIEWS: [(V_IMP_OLD, V_IMP_NEW), (V_ALL_OLD, V_ALL_NEW),
                (V_TAIL_OLD, V_TAIL_OLD + V_NEW)],
        URLS: [(U_OLD, U_NEW)],
        LIST_TPL: [(T_OLD, T_NEW)],
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

    print("done. copy customer_invoice_form.html into pages/templates/, then:")
    print("  python manage.py check")
    print("  use 'New Customer Invoice' on the Physical Invoices screen")


if __name__ == "__main__":
    main()