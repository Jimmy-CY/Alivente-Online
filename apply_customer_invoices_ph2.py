# -*- coding: utf-8 -*-
"""
Apply: Phase 2 of customer (non-tenant) invoices — the customer book CRUD.

  pages/views/physical_invoices.py
    + import ProtectedError and InvoiceCustomer
    + add 4 names to __all__
    + append customer_list / customer_add / customer_edit / customer_delete
      (+ the _customer_post helper)

  pages/urls.py  (INVOICES block)
    + invoice-customers/                      -> customer_list
    + invoice-customers/add/                  -> customer_add
    + invoice-customers/<id>/edit/            -> customer_edit
    + invoice-customers/<id>/delete/          -> customer_delete

  pages/templates/physical_invoice_list.html
    + a "Manage Customers" button on the action row

Templates customer_list.html and customer_form.html are delivered separately
and must be copied into pages/templates/.

Permissions: can_access_tenants (view) / can_edit_tenants (add/edit/delete).
Delete is PROTECT-guarded: a customer with invoices can't be deleted; the view
catches ProtectedError and shows a friendly message.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check
Then visit:     /invoice-customers/   (or the "Manage Customers" button)

Run from the repo root:  python apply_customer_invoices_ph2.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
URLS = os.path.join("pages", "urls.py")
LIST_TPL = os.path.join("pages", "templates", "physical_invoice_list.html")

# ---------------------------------------------------------------- views.py
V_IMP_OLD = "from pages.models import PhysicalInvoice, PhysicalInvoiceLine, PhysicalInvoiceNumbering"
V_IMP_NEW = ("from django.db.models import ProtectedError\n"
             "from pages.models import (\n"
             "    InvoiceCustomer, PhysicalInvoice, PhysicalInvoiceLine, PhysicalInvoiceNumbering,\n"
             ")")

V_ALL_OLD = '    "physical_invoice_set_next_number",\n]'
V_ALL_NEW = ('    "physical_invoice_set_next_number",\n'
             '    "customer_list",\n'
             '    "customer_add",\n'
             '    "customer_edit",\n'
             '    "customer_delete",\n'
             ']')

V_TAIL_OLD = '''    nxt = request.POST.get("next") or ""
    if nxt and url_has_allowed_host_and_scheme(
            nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)
    return redirect(reverse("physical_invoice_list"))'''

V_NEW_VIEWS = '''


# ------------------------------------------------------------------ #
# Invoice customers (non-tenant billing book)
# ------------------------------------------------------------------ #
def _customer_post(request, obj):
    """Copy the submitted customer fields onto obj (unsaved). Shared by add/edit."""
    obj.name = (request.POST.get("name") or "").strip()[:255]
    obj.customer_id_label = (request.POST.get("customer_id_label") or "").strip()[:255]
    obj.billing_address = (request.POST.get("billing_address") or "").strip()
    obj.billing_tel = (request.POST.get("billing_tel") or "").strip()[:64]
    obj.email_to = (request.POST.get("email_to") or "").strip()
    obj.email_cc = (request.POST.get("email_cc") or "").strip()
    obj.email_body = (request.POST.get("email_body") or "").strip()
    return obj


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def customer_list(request):
    """The saved invoice-customer book."""
    customers = InvoiceCustomer.objects.all().order_by("name")
    rows = []
    for c in customers:
        rows.append({
            "pk": c.pk,
            "name": c.name,
            "customer_id_label": c.customer_id_label,
            "email_to": c.email_to,
            "invoice_count": c.invoices.count(),
        })
    return render(request, "customer_list.html", {"rows": rows})


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def customer_add(request):
    """Create a new invoice customer."""
    if request.method == "POST":
        obj = _customer_post(request, InvoiceCustomer())
        if not obj.name:
            messages.error(request, "A customer name is required.")
            return render(request, "customer_form.html",
                          {"mode": "add", "form_data": request.POST})
        obj.save()
        messages.success(request, f"Customer '{obj.name}' added.")
        return redirect("customer_list")
    return render(request, "customer_form.html", {"mode": "add", "form_data": {}})


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def customer_edit(request, customer_id):
    """Edit an existing invoice customer."""
    obj = get_object_or_404(InvoiceCustomer, pk=customer_id)
    if request.method == "POST":
        _customer_post(request, obj)
        if not obj.name:
            messages.error(request, "A customer name is required.")
            return render(request, "customer_form.html",
                          {"mode": "edit", "customer": obj, "form_data": request.POST})
        obj.save()
        messages.success(request, f"Customer '{obj.name}' updated.")
        return redirect("customer_list")
    return render(request, "customer_form.html",
                  {"mode": "edit", "customer": obj, "form_data": obj})


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def customer_delete(request, customer_id):
    """Delete a customer. PROTECT blocks deletion if any invoice references it."""
    obj = get_object_or_404(InvoiceCustomer, pk=customer_id)
    name = obj.name
    try:
        obj.delete()
        messages.success(request, f"Customer '{name}' deleted.")
    except ProtectedError:
        n = obj.invoices.count()
        messages.error(
            request,
            f"'{name}' has {n} invoice{'' if n == 1 else 's'} and can't be deleted. "
            f"Customers with invoices are kept so the invoices stay intact.")
    return redirect("customer_list")
'''

# ---------------------------------------------------------------- urls.py
U_OLD = '    path("physical-invoices/set-next-number/", views.physical_invoice_set_next_number, name="physical_invoice_set_next_number"),'
U_NEW = (U_OLD + '\n'
         '    path("invoice-customers/", views.customer_list, name="customer_list"),\n'
         '    path("invoice-customers/add/", views.customer_add, name="customer_add"),\n'
         '    path("invoice-customers/<int:customer_id>/edit/", views.customer_edit, name="customer_edit"),\n'
         '    path("invoice-customers/<int:customer_id>/delete/", views.customer_delete, name="customer_delete"),')

# ---------------------------------------------------------------- list template
T_OLD = '''    <div class="page-action-buttons">
      <a href="{% url 'tenant' %}" class="btn btn-info action-back" aria-label="Back to tenants">'''
T_NEW = '''    <div class="page-action-buttons">
      {% if perms.auth.can_access_tenants %}
        <a href="{% url 'customer_list' %}" class="btn btn-info action-secondary">
          <i class="fas fa-address-book"></i> Manage Customers
        </a>
      {% endif %}
      <a href="{% url 'tenant' %}" class="btn btn-info action-back" aria-label="Back to tenants">'''


def _load(path):
    if not os.path.exists(path):
        return None
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def main():
    targets = {
        VIEWS: [(V_IMP_OLD, V_IMP_NEW), (V_ALL_OLD, V_ALL_NEW),
                (V_TAIL_OLD, V_TAIL_OLD + V_NEW_VIEWS)],
        URLS: [(U_OLD, U_NEW)],
        LIST_TPL: [(T_OLD, T_NEW)],
    }

    # Verify all anchors before writing anything.
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

    # Apply + (for .py) parse-check.
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

    print("done. copy customer_list.html + customer_form.html into pages/templates/, then:")
    print("  python manage.py check")
    print("  visit /invoice-customers/ (or the 'Manage Customers' button)")


if __name__ == "__main__":
    main()