# -*- coding: utf-8 -*-
"""
Apply: Approve / Un-approve actions (stage 3 of the Approve/Edit screen) - BACKEND.

  pages/views/physical_invoices.py
    + imports: ValidationError, reverse, url_has_allowed_host_and_scheme, require_POST
    + add the two view names to __all__
    + append _redirect_after_pi_action, physical_invoice_approve,
      physical_invoice_unapprove (POST-only, gated by auth.can_edit_tenants).

  pages/urls.py
    + routes physical-invoices/<id>/approve/ and /unapprove/

The two templates (physical_invoice_list.html, physical_invoice_edit.html) are
delivered separately as full drop-ins.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_pi_approve_stage3.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
URLS = os.path.join("pages", "urls.py")

NEW_VIEWS = '''

def _redirect_after_pi_action(request, pi):
    """Return to ?next= if it is a safe in-site path, else the list for the
    invoice's own period."""
    nxt = request.POST.get("next") or ""
    if nxt and url_has_allowed_host_and_scheme(
            nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)
    base = reverse("physical_invoice_list")
    return redirect(f"{base}?period={pi.period_year:04d}-{pi.period_month:02d}")


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def physical_invoice_approve(request, physical_invoice_id):
    """Move a draft invoice to approved (the state the send cron sends from)."""
    pi = get_object_or_404(PhysicalInvoice, pk=physical_invoice_id)
    try:
        pi.approve(user=request.user)
        messages.success(request, f"Invoice for {pi.tenant.tenant_name} approved.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
    return _redirect_after_pi_action(request, pi)


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def physical_invoice_unapprove(request, physical_invoice_id):
    """Move an approved (not yet sent) invoice back to draft."""
    pi = get_object_or_404(PhysicalInvoice, pk=physical_invoice_id)
    try:
        pi.unapprove()
        messages.success(request, f"Invoice for {pi.tenant.tenant_name} moved back to draft.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
    return _redirect_after_pi_action(request, pi)
'''

VIEWS_EDITS = [
    ("from django.core.exceptions import ObjectDoesNotExist",
     "from django.core.exceptions import ObjectDoesNotExist, ValidationError"),
    ("from django.template.loader import render_to_string",
     "from django.template.loader import render_to_string\n"
     "from django.urls import reverse\n"
     "from django.utils.http import url_has_allowed_host_and_scheme\n"
     "from django.views.decorators.http import require_POST"),
    ('    "physical_invoice_edit",\n]',
     '    "physical_invoice_edit",\n'
     '    "physical_invoice_approve",\n'
     '    "physical_invoice_unapprove",\n]'),
    ('    return render(request, "physical_invoice_edit.html", context)',
     '    return render(request, "physical_invoice_edit.html", context)' + NEW_VIEWS),
]

URLS_EDITS = [
    ('    path("physical-invoices/<int:physical_invoice_id>/edit/", views.physical_invoice_edit, name="physical_invoice_edit"),',
     '    path("physical-invoices/<int:physical_invoice_id>/edit/", views.physical_invoice_edit, name="physical_invoice_edit"),\n'
     '    path("physical-invoices/<int:physical_invoice_id>/approve/", views.physical_invoice_approve, name="physical_invoice_approve"),\n'
     '    path("physical-invoices/<int:physical_invoice_id>/unapprove/", views.physical_invoice_unapprove, name="physical_invoice_unapprove"),'),
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

    print("done. next: check")


if __name__ == "__main__":
    main()