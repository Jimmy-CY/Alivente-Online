# -*- coding: utf-8 -*-
"""
Apply: delete DRAFT physical invoices (tenant + customer).

  pages/views/physical_invoices.py
    + "physical_invoice_delete" in __all__
    + physical_invoice_delete() view: draft-only guard; removes line rows + the
      stored PDF + the invoice row; works for tenant and customer invoices.
      (Drafts hold no PR number, so no counter gap.)

  pages/urls.py
    + physical-invoices/<id>/delete/ -> physical_invoice_delete

  pages/templates/physical_invoice_list.html
    + Delete button on the row Actions (desktop + mobile), DRAFT rows only
    + .icon-trash / .icon-color-trash styles

  pages/templates/customer_invoice_form.html
    + Delete button in the action row on a DRAFT customer invoice
    + .btn-delete style

  pages/templates/physical_invoice_edit.html
    + Delete button in the action row on a DRAFT tenant invoice
    + .btn-delete style

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_physical_invoice_delete.py
"""
import ast
import io
import os
import sys

VIEWS = os.path.join("pages", "views", "physical_invoices.py")
URLS = os.path.join("pages", "urls.py")
LIST_TPL = os.path.join("pages", "templates", "physical_invoice_list.html")
CFORM_TPL = os.path.join("pages", "templates", "customer_invoice_form.html")
TFORM_TPL = os.path.join("pages", "templates", "physical_invoice_edit.html")

# ----------------------------------------------------------------- views.py
V_ALL_OLD = '    "customer_invoice_duplicate",\n]'
V_ALL_NEW = '    "customer_invoice_duplicate",\n    "physical_invoice_delete",\n]'

V_APPEND_ANCHOR = '    return redirect("customer_invoice_edit", physical_invoice_id=new_pi.pk)'
V_NEW = '''


# ------------------------------------------------------------------ #
# Delete a DRAFT invoice (tenant or customer)
# ------------------------------------------------------------------ #
@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def physical_invoice_delete(request, physical_invoice_id):
    """Delete a DRAFT invoice (tenant or customer). Removes the line rows and the
    stored PDF (if any) along with the invoice. Only drafts are deletable; an
    approved/sent invoice must be un-approved back to draft first. Drafts hold no
    PR number, so deleting one never leaves a gap in the sequence."""
    pi = get_object_or_404(PhysicalInvoice, pk=physical_invoice_id)

    def _back():
        nxt = request.POST.get("next") or ""
        if nxt and url_has_allowed_host_and_scheme(
                nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(nxt)
        return redirect(reverse("physical_invoice_list"))

    if pi.status != PhysicalInvoice.STATUS_DRAFT:
        messages.error(
            request,
            f"Only a draft invoice can be deleted. {_pi_who(pi)}'s invoice is "
            f"{pi.get_status_display()} \\u2014 un-approve it back to draft first.")
        return _back()

    who = _pi_who(pi)
    with transaction.atomic():
        try:
            if pi.pdf_file:
                pi.pdf_file.delete(save=False)
        except Exception:
            pass
        pi.lines.all().delete()
        pi.delete()

    messages.success(request, f"Draft invoice for {who or 'the customer'} deleted.")
    return _back()'''

# ----------------------------------------------------------------- urls.py
U_OLD = '    path("invoice-customers/invoice/<int:physical_invoice_id>/duplicate/", views.customer_invoice_duplicate, name="customer_invoice_duplicate"),'
U_NEW = (U_OLD + '\n'
         '    path("physical-invoices/<int:physical_invoice_id>/delete/", views.physical_invoice_delete, name="physical_invoice_delete"),')

# ----------------------------------------------- list template: desktop delete button
# Insert before the desktop PDF link (unique by icon-view class).
LT_DESK_OLD = '''              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="icon-action-btn icon-view" title="View invoice PDF">
                <i class="fas fa-file-pdf"></i>
              </a>'''
LT_DESK_NEW = '''              {% if perms.auth.can_edit_tenants and row.status == 'draft' %}
                <form method="post" action="{% url 'physical_invoice_delete' row.pk %}" class="pi-inline-form"
                      onsubmit="return confirm('Delete this draft invoice? This cannot be undone.');">
                  {% csrf_token %}
                  <input type="hidden" name="next" value="{{ request.get_full_path }}">
                  <button type="submit" class="icon-action-btn icon-trash" title="Delete draft">
                    <i class="fas fa-trash"></i>
                  </button>
                </form>
              {% endif %}
              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="icon-action-btn icon-view" title="View invoice PDF">
                <i class="fas fa-file-pdf"></i>
              </a>'''

# ----------------------------------------------- list template: mobile delete button
LT_MOB_OLD = '''              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="mobile-action-btn">
                <i class="fas fa-file-pdf mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View PDF</span>
              </a>'''
LT_MOB_NEW = '''              {% if perms.auth.can_edit_tenants and row.status == 'draft' %}
                <form method="post" action="{% url 'physical_invoice_delete' row.pk %}" class="pi-inline-form-mobile"
                      onsubmit="return confirm('Delete this draft invoice? This cannot be undone.');">
                  {% csrf_token %}
                  <input type="hidden" name="next" value="{{ request.get_full_path }}">
                  <button type="submit" class="mobile-action-btn">
                    <i class="fas fa-trash mobile-action-icon icon-color-trash"></i>
                    <span class="mobile-action-label">Delete</span>
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
LT_CSS_OLD = ".icon-duplicate { color: #6f42c1; border-color: #6f42c1; }\n.icon-duplicate:hover { background-color: #6f42c1; color: white; }"
LT_CSS_NEW = (".icon-duplicate { color: #6f42c1; border-color: #6f42c1; }\n"
              ".icon-duplicate:hover { background-color: #6f42c1; color: white; }\n"
              ".icon-trash { color: #dc3545; border-color: #dc3545; }\n"
              ".icon-trash:hover { background-color: #dc3545; color: white; }")

# ----------------------------------------------- list template: mobile colour CSS
LT_MCSS_OLD = "  .icon-color-duplicate { color: #6f42c1; }"
LT_MCSS_NEW = "  .icon-color-duplicate { color: #6f42c1; }\n  .icon-color-trash { color: #dc3545; }"

# ------------------------------------------- customer form: delete button (draft) + CSS
CF_OLD = '''  <div class="status-action-row">
    {% if pi.status != 'draft' %}'''
CF_NEW = '''  <div class="status-action-row">
    {% if pi.status == 'draft' %}
    <form method="post" action="{% url 'physical_invoice_delete' pi.pk %}" class="status-action-form"
          onsubmit="return confirm('Delete this draft invoice? This cannot be undone.');">
      {% csrf_token %}
      <input type="hidden" name="next" value="{% url 'physical_invoice_list' %}">
      <button type="submit" class="btn btn-delete">
        <i class="fas fa-trash"></i> Delete
      </button>
    </form>
    {% endif %}
    {% if pi.status != 'draft' %}'''

CF_CSS_OLD = ".btn-duplicate:hover { background-color: #5e37a6; border-color: #563098; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }"
CF_CSS_NEW = (".btn-duplicate:hover { background-color: #5e37a6; border-color: #563098; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }\n"
              ".btn-delete { background-color: #dc3545; color: white; border: 1px solid #dc3545; border-radius: 6px; font-weight: 500; padding: 8px 18px; transition: all 0.2s ease; }\n"
              ".btn-delete:hover { background-color: #c82333; border-color: #bd2130; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }")

# ------------------------------------------- tenant form (physical_invoice_edit.html): delete (draft) + CSS
# Insert a Delete form at the start of the status-action-row (draft only).
TF_OLD = '''  <div class="status-action-row">
    {% if pi.status == 'draft' %}
      <form method="post" action="{% url 'physical_invoice_approve' pi.pk %}" class="status-action-form">'''
TF_NEW = '''  <div class="status-action-row">
    {% if pi.status == 'draft' %}
      <form method="post" action="{% url 'physical_invoice_delete' pi.pk %}" class="status-action-form"
            onsubmit="return confirm('Delete this draft invoice? This cannot be undone.');">
        {% csrf_token %}
        <input type="hidden" name="next" value="{% url 'physical_invoice_list' %}">
        <button type="submit" class="btn btn-delete">
          <i class="fas fa-trash"></i> Delete
        </button>
      </form>
      <form method="post" action="{% url 'physical_invoice_approve' pi.pk %}" class="status-action-form">'''

TF_CSS_OLD = ".btn-unapprove:hover { background-color: #e8690b; border-color: #d9610a; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }"
TF_CSS_NEW = (".btn-unapprove:hover { background-color: #e8690b; border-color: #d9610a; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }\n"
              ".btn-delete { background-color: #dc3545; color: white; border: 1px solid #dc3545; border-radius: 6px; font-weight: 500; padding: 8px 18px; transition: all 0.2s ease; }\n"
              ".btn-delete:hover { background-color: #c82333; border-color: #bd2130; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }")

# Tenant form: add gap to its status-action-row too (so Delete + Approve don't touch).
TF_ROW_OLD = ".status-action-row { display: flex; justify-content: flex-end; margin-top: 20px; }"
TF_ROW_NEW = ".status-action-row { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; flex-wrap: wrap; }"


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
        CFORM_TPL: [(CF_OLD, CF_NEW), (CF_CSS_OLD, CF_CSS_NEW)],
        TFORM_TPL: [(TF_OLD, TF_NEW), (TF_CSS_OLD, TF_CSS_NEW), (TF_ROW_OLD, TF_ROW_NEW)],
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