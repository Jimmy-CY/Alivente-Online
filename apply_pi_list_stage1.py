# -*- coding: utf-8 -*-
"""
Apply: Physical Invoices read-only list (stage 1 of the Approve/Edit screen).

  pages/views/physical_invoices.py
    + import permission_required and render
    + import preview_batch_numbers
    + add "physical_invoice_list" to __all__
    + append the physical_invoice_list view (gated by auth.can_access_tenants)

  pages/urls.py
    + route physical-invoices/list/ -> physical_invoice_list

The template pages/templates/physical_invoice_list.html is delivered separately.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check
Then visit:    /physical-invoices/list/   (defaults to the upcoming month)

Run from the repo root:  python apply_pi_list_stage1.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
URLS = os.path.join("pages", "urls.py")

NEW_VIEW = '''

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def physical_invoice_list(request):
    """Read-only list of physical invoices for one month.

    Defaults to the upcoming month (where the prepare cron seeds drafts);
    accepts ?period=YYYY-MM and ?status=draft|approved|sent. Draft and approved
    rows show their provisional PR number; sent rows show the assigned number.
    """
    raw = (request.GET.get("period") or "").strip()
    period_first = None
    if raw:
        try:
            y, m = raw.split("-")
            period_first = date(int(y), int(m), 1)
        except (ValueError, TypeError):
            period_first = None
    if period_first is None:
        period_first = _upcoming_period()
    y, m = period_first.year, period_first.month

    base = PhysicalInvoice.objects.filter(period_year=y, period_month=m)
    counts = {
        "draft": base.filter(status=PhysicalInvoice.STATUS_DRAFT).count(),
        "approved": base.filter(status=PhysicalInvoice.STATUS_APPROVED).count(),
        "sent": base.filter(status=PhysicalInvoice.STATUS_SENT).count(),
    }

    status = (request.GET.get("status") or "").strip()
    qs = base.select_related("tenant", "tenant__prop").order_by("tenant__tenant_name")
    if status in (PhysicalInvoice.STATUS_DRAFT, PhysicalInvoice.STATUS_APPROVED,
                  PhysicalInvoice.STATUS_SENT):
        qs = qs.filter(status=status)

    provisional = preview_batch_numbers(
        y, m, statuses=(PhysicalInvoice.STATUS_DRAFT, PhysicalInvoice.STATUS_APPROVED))

    rows = []
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
        })

    context = {
        "rows": rows,
        "counts": counts,
        "period_value": f"{y:04d}-{m:02d}",
        "period_label": period_first.strftime("%B %Y"),
        "status": status,
    }
    return render(request, "physical_invoice_list.html", context)
'''

VIEWS_EDITS = [
    ("from django.contrib.auth.decorators import login_required",
     "from django.contrib.auth.decorators import login_required, permission_required"),
    ("from django.shortcuts import get_object_or_404",
     "from django.shortcuts import get_object_or_404, render"),
    ("from pages.models import PhysicalInvoice",
     "from pages.models import PhysicalInvoice\nfrom pages.services.physical_invoice_numbering import preview_batch_numbers"),
    ('    "render_physical_invoice_pdf",\n]',
     '    "render_physical_invoice_pdf",\n    "physical_invoice_list",\n]'),
    ('''    fname = (pi.invoice_number or f"draft-{pi.pk}").replace(" ", "_")
    response["Content-Disposition"] = f'inline; filename="invoice_{fname}.pdf"'
    return response''',
     '''    fname = (pi.invoice_number or f"draft-{pi.pk}").replace(" ", "_")
    response["Content-Disposition"] = f'inline; filename="invoice_{fname}.pdf"'
    return response''' + NEW_VIEW),
]

URLS_EDITS = [
    ('    path("physical-invoices/<int:physical_invoice_id>/pdf/", views.render_stored_invoice_pdf, name="physical_invoice_pdf"),',
     '    path("physical-invoices/<int:physical_invoice_id>/pdf/", views.render_stored_invoice_pdf, name="physical_invoice_pdf"),\n'
     '    path("physical-invoices/list/", views.physical_invoice_list, name="physical_invoice_list"),'),
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
    targets = [(VIEWS, VIEWS_EDITS), (URLS, URLS_EDITS)]
    loaded, all_problems = [], []
    for path, edits in targets:
        src, problems = _verify(path, edits)
        all_problems.extend(problems)
        loaded.append((path, edits, src))
    if all_problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(all_problems))

    results = []
    for path, edits, src in loaded:
        new_src = src
        for old, new in edits:
            new_src = new_src.replace(old, new, 1)
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

    print("done. next: check, then visit /physical-invoices/list/")


if __name__ == "__main__":
    main()