# -*- coding: utf-8 -*-
"""
Apply: Physical Invoice edit-lines screen (stage 2 of the Approve/Edit screen).

  pages/views/physical_invoices.py
    + imports: Decimal, messages, transaction, redirect, PhysicalInvoiceLine
    + add "physical_invoice_edit" to __all__
    + append the physical_invoice_edit view (gated by auth.can_edit_tenants);
      Save replaces the line rows from the submitted arrays and recalc_totals().

  pages/urls.py
    + route physical-invoices/<id>/edit/ -> physical_invoice_edit

  pages/templates/physical_invoice_list.html
    + the invoice Number becomes a link to the edit screen

Template pages/templates/physical_invoice_edit.html is delivered separately.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_pi_edit_stage2.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
URLS = os.path.join("pages", "urls.py")
LIST_TPL = os.path.join("pages", "templates", "physical_invoice_list.html")

NEW_VIEW = '''

@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def physical_invoice_edit(request, physical_invoice_id):
    """Edit the line rows of a DRAFT physical invoice; Save recomputes totals.

    Approved/sent invoices are read-only here (un-approve first). Lines are
    replaced wholesale from the submitted parallel arrays, then recalc_totals()
    refreshes subtotal/VAT/total on the invoice.
    """
    pi = get_object_or_404(
        PhysicalInvoice.objects.select_related("tenant", "tenant__prop"),
        pk=physical_invoice_id)

    if request.method == "POST":
        if not pi.is_editable:
            messages.error(
                request,
                f"Invoice {pi.invoice_number or pi.pk} is {pi.get_status_display()} "
                f"and cannot be edited. Un-approve it first.")
            return redirect("physical_invoice_edit", physical_invoice_id=pi.pk)

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
                continue  # skip an empty add-row stub
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

        messages.success(
            request,
            f"Invoice for {pi.tenant.tenant_name} saved "
            f"({pi.currency} {_money(pi.total)}).")
        return redirect("physical_invoice_edit", physical_invoice_id=pi.pk)

    provisional = preview_batch_numbers(
        pi.period_year, pi.period_month,
        statuses=(PhysicalInvoice.STATUS_DRAFT, PhysicalInvoice.STATUS_APPROVED))
    context = {
        "pi": pi,
        "lines": pi.lines.all(),
        "number": pi.invoice_number or provisional.get(pi.pk, "\\u2014"),
        "property_name": getattr(pi.tenant.prop, "prop_name", "") or "",
        "period_label": date(pi.period_year, pi.period_month, 1).strftime("%B %Y"),
        "vat_rate_display": f"{float(pi.vat_rate) * 100:.2f}%",
        "subtotal_display": _money(pi.subtotal),
        "vat_display": _money(pi.vat),
        "total_display": _money(pi.total),
        "is_editable": pi.is_editable,
    }
    return render(request, "physical_invoice_edit.html", context)
'''

VIEWS_EDITS = [
    ("from datetime import date",
     "from datetime import date\nfrom decimal import Decimal"),
    ("from django.contrib.auth.decorators import login_required, permission_required",
     "from django.contrib.auth.decorators import login_required, permission_required\nfrom django.contrib import messages"),
    ("from django.core.exceptions import ObjectDoesNotExist",
     "from django.core.exceptions import ObjectDoesNotExist\nfrom django.db import transaction"),
    ("from django.shortcuts import get_object_or_404, render",
     "from django.shortcuts import get_object_or_404, redirect, render"),
    ("from pages.models import PhysicalInvoice\nfrom pages.services.physical_invoice_numbering import preview_batch_numbers",
     "from pages.models import PhysicalInvoice, PhysicalInvoiceLine\nfrom pages.services.physical_invoice_numbering import preview_batch_numbers"),
    ('    "physical_invoice_list",\n]',
     '    "physical_invoice_list",\n    "physical_invoice_edit",\n]'),
    ('    return render(request, "physical_invoice_list.html", context)',
     '    return render(request, "physical_invoice_list.html", context)' + NEW_VIEW),
]

URLS_EDITS = [
    ('    path("physical-invoices/list/", views.physical_invoice_list, name="physical_invoice_list"),',
     '    path("physical-invoices/list/", views.physical_invoice_list, name="physical_invoice_list"),\n'
     '    path("physical-invoices/<int:physical_invoice_id>/edit/", views.physical_invoice_edit, name="physical_invoice_edit"),'),
]

LIST_EDITS = [
    ('            <td data-label="Number" class="pi-number">{{ row.number }}</td>',
     '            <td data-label="Number" class="pi-number">\n'
     '              <a href="{% url \'physical_invoice_edit\' row.pk %}" class="pi-number-link">{{ row.number }}</a>\n'
     '            </td>'),
    ('.pi-number { font-weight: 600; color: #2c3e50; }',
     '.pi-number { font-weight: 600; color: #2c3e50; }\n'
     '.pi-number-link { color: #17a2b8; text-decoration: none; font-weight: 600; }\n'
     '.pi-number-link:hover { text-decoration: underline; }'),
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
    targets = [(VIEWS, VIEWS_EDITS, True), (URLS, URLS_EDITS, True), (LIST_TPL, LIST_EDITS, False)]
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