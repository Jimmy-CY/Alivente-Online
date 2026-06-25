# -*- coding: utf-8 -*-
"""
Apply: Phase 5b step 2 — customer-invoice Send-now.

  pages/views/physical_invoices.py
    + imports: ContentFile, slugify, suggested_next_number, and the shared
      invoice_email service (assemble_bodies, load_logo, send_invoice_email)
    + "customer_invoice_send" in __all__
    ~ list row "number": customer invoices show "(on send)" until actually sent
    + GENERIC_CUSTOMER_BODY, _split_addrs(), customer_invoice_send() view

  pages/urls.py
    + invoice-customers/invoice/<id>/send/  -> customer_invoice_send

  pages/templates/physical_invoice_list.html
    + Send-now button on the row Actions (desktop + mobile), approved customer only
    + .icon-send / .icon-color-send styles

  pages/templates/customer_invoice_form.html
    + Send-now button next to Un-approve on the edit screen (approved)
    + .btn-send style

Send view: customer-only + approved guard; numbers at send (atomic counter,
select_for_update); renders + stores the PDF; e-mails via the shared service to
the bill_* snapshot To/CC with subject "Alivente Limited (Invoice PR-####)" and
the bill_email_body (or a generic default) + footer; marks sent only on success.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_customer_invoices_ph5b_send.py
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
V_I1_OLD = "from django.core.exceptions import ObjectDoesNotExist, ValidationError\nfrom django.db import transaction"
V_I1_NEW = "from django.core.exceptions import ObjectDoesNotExist, ValidationError\nfrom django.core.files.base import ContentFile\nfrom django.db import transaction"

V_I2_OLD = "from django.utils.http import url_has_allowed_host_and_scheme"
V_I2_NEW = "from django.utils.http import url_has_allowed_host_and_scheme\nfrom django.utils.text import slugify"

V_I3_OLD = "from pages.services.physical_invoice_numbering import preview_batch_numbers"
V_I3_NEW = ("from pages.services.invoice_email import assemble_bodies, load_logo, send_invoice_email\n"
            "from pages.services.physical_invoice_numbering import preview_batch_numbers, suggested_next_number")

V_ALL_OLD = '    "customer_invoice_edit",\n]'
V_ALL_NEW = '    "customer_invoice_edit",\n    "customer_invoice_send",\n]'

V_ROW_OLD = '            "number": pi.invoice_number or provisional.get(pi.pk, "\\u2014"),'
V_ROW_NEW = '            "number": pi.invoice_number or ("(on send)" if is_customer else provisional.get(pi.pk, "\\u2014")),'

V_APPEND_ANCHOR = '''        "total_display": _money(pi.total),
        "is_editable": pi.is_editable,
    })
    return render(request, "customer_invoice_form.html", ctx)'''

V_NEW = '''


# ------------------------------------------------------------------ #
# Customer invoice: Send now (on-demand, customer-only)
# ------------------------------------------------------------------ #
GENERIC_CUSTOMER_BODY = (
    "To Whom It May Concern,\\n\\n"
    "Please find attached our latest invoice."
)


def _split_addrs(raw):
    """Comma/semicolon-separated address text -> clean de-duped list (order kept)."""
    if not raw:
        return []
    out, seen = [], set()
    for part in raw.replace(";", ",").split(","):
        p = part.strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def customer_invoice_send(request, physical_invoice_id):
    """Send one APPROVED customer (non-tenant) invoice on demand: number it at
    send (atomic, shared counter), render + store the PDF, e-mail it via the
    shared invoice-email service to the bill_* snapshot To/CC, and mark it sent
    only on a successful e-mail."""
    pi = get_object_or_404(PhysicalInvoice, pk=physical_invoice_id)

    def _back():
        nxt = request.POST.get("next") or ""
        if nxt and url_has_allowed_host_and_scheme(
                nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(nxt)
        return redirect(reverse("physical_invoice_list"))

    if pi.tenant_id is not None:
        messages.error(request, "Send-now is only for customer invoices.")
        return _back()
    if pi.status != PhysicalInvoice.STATUS_APPROVED:
        messages.error(request, "Only an approved customer invoice can be sent. Approve it first.")
        return _back()

    to_list = _split_addrs(pi.bill_email_to)
    cc_list = _split_addrs(pi.bill_email_cc)
    if not pi.lines.exists():
        messages.error(request, "This invoice has no lines to send.")
        return _back()
    if not to_list:
        messages.error(request, "This customer has no 'Email To' address; add one before sending.")
        return _back()

    # 1) Number at send: atomic read-and-advance of the shared counter.
    if not pi.invoice_number:
        with transaction.atomic():
            cfg = (PhysicalInvoiceNumbering.objects
                   .select_for_update().get(pk=PhysicalInvoiceNumbering.get_solo().pk))
            n = suggested_next_number(cfg)
            pi.invoice_number = cfg.format(n)
            pi.save(update_fields=["invoice_number", "updated_at"])
            cfg.next_number = n + 1
            cfg.save(update_fields=["next_number", "updated_at"])

    # 2) Render + store the PDF (same path as the preview).
    try:
        context = build_context_from_invoice(pi)
        pdf_bytes = render_physical_invoice_pdf(context)
        base = slugify(pi.invoice_number or f"draft-{pi.pk}")
        pi.pdf_file.save(f"{base}.pdf", ContentFile(pdf_bytes), save=True)
    except Exception as exc:
        messages.error(request, f"Could not render the invoice PDF: {exc}")
        return _back()

    # 3) E-mail via the shared service. The first To is the visible recipient;
    #    any further To addresses are delivered alongside the CC list.
    core = (pi.bill_email_body or "").strip() or GENERIC_CUSTOMER_BODY
    logo_bytes = load_logo()
    text_body, html_body = assemble_bodies(core, include_logo=logo_bytes is not None)
    subject = f"Alivente Limited (Invoice {pi.invoice_number})"
    filename = f"{pi.invoice_number} - {(pi.bill_name or 'customer')}.pdf"
    extra_recipients = to_list[1:] + cc_list

    try:
        send_invoice_email(to_list[0], extra_recipients, subject,
                           text_body, html_body, pdf_bytes, filename, logo_bytes)
    except Exception as exc:
        if hasattr(pi, "email_status"):
            pi.email_status = "failed"
            pi.save(update_fields=["email_status", "updated_at"])
        messages.error(
            request,
            f"Invoice {pi.invoice_number} could not be e-mailed ({exc}); it stays "
            f"approved (and numbered) so you can retry.")
        return _back()

    if hasattr(pi, "email_status"):
        pi.email_status = "sent"
    pi.mark_sent()
    messages.success(
        request,
        f"Invoice {pi.invoice_number} sent to {to_list[0]}"
        + (f" (+{len(extra_recipients)} more)" if extra_recipients else "") + ".")
    return _back()'''

# ----------------------------------------------------------------- urls.py
U_OLD = '    path("invoice-customers/invoice/<int:physical_invoice_id>/edit/", views.customer_invoice_edit, name="customer_invoice_edit"),'
U_NEW = (U_OLD + '\n'
         '    path("invoice-customers/invoice/<int:physical_invoice_id>/send/", views.customer_invoice_send, name="customer_invoice_send"),')

# ------------------------------------------------------- list template: desktop send button
LT_DESK_OLD = '''              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="icon-action-btn icon-view" title="View invoice PDF">
                <i class="fas fa-file-pdf"></i>
              </a>'''
LT_DESK_NEW = '''              {% if perms.auth.can_edit_tenants and row.is_customer and row.status == 'approved' %}
                <form method="post" action="{% url 'customer_invoice_send' row.pk %}" class="pi-inline-form"
                      onsubmit="return confirm('Send this invoice now? It will be numbered and e-mailed to the customer.');">
                  {% csrf_token %}
                  <input type="hidden" name="next" value="{{ request.get_full_path }}">
                  <button type="submit" class="icon-action-btn icon-send" title="Send now">
                    <i class="fas fa-paper-plane"></i>
                  </button>
                </form>
              {% endif %}
              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="icon-action-btn icon-view" title="View invoice PDF">
                <i class="fas fa-file-pdf"></i>
              </a>'''

# ------------------------------------------------------- list template: mobile send button
LT_MOB_OLD = '''              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="mobile-action-btn">
                <i class="fas fa-file-pdf mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View PDF</span>
              </a>'''
LT_MOB_NEW = '''              {% if perms.auth.can_edit_tenants and row.is_customer and row.status == 'approved' %}
                <form method="post" action="{% url 'customer_invoice_send' row.pk %}" class="pi-inline-form-mobile"
                      onsubmit="return confirm('Send this invoice now? It will be numbered and e-mailed to the customer.');">
                  {% csrf_token %}
                  <input type="hidden" name="next" value="{{ request.get_full_path }}">
                  <button type="submit" class="mobile-action-btn">
                    <i class="fas fa-paper-plane mobile-action-icon icon-color-send"></i>
                    <span class="mobile-action-label">Send</span>
                  </button>
                </form>
              {% endif %}
              <a href="{% url 'physical_invoice_pdf' row.pk %}"
                 onclick="openPdfViewer('{% url 'physical_invoice_pdf' row.pk %}', 'Invoice {{ row.number|escapejs }} &mdash; {{ row.tenant|escapejs }}', '{{ row.number|escapejs }}.pdf'); return false;"
                 class="mobile-action-btn">
                <i class="fas fa-file-pdf mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View PDF</span>
              </a>'''

# ------------------------------------------------------- list template: desktop icon CSS
LT_CSS_OLD = ".icon-unapprove { color: #fd7e14; border-color: #fd7e14; }\n.icon-unapprove:hover { background-color: #fd7e14; color: white; }"
LT_CSS_NEW = (".icon-unapprove { color: #fd7e14; border-color: #fd7e14; }\n"
              ".icon-unapprove:hover { background-color: #fd7e14; color: white; }\n"
              ".icon-send { color: #007bff; border-color: #007bff; }\n"
              ".icon-send:hover { background-color: #007bff; color: white; }")

# ------------------------------------------------------- list template: mobile colour CSS
LT_MCSS_OLD = "  .icon-color-unapprove { color: #fd7e14; }"
LT_MCSS_NEW = "  .icon-color-unapprove { color: #fd7e14; }\n  .icon-color-send { color: #007bff; }"

# ----------------------------------------------------- form template: edit-screen send button
FT_OLD = '''    {% elif pi.status == 'approved' %}
      <form method="post" action="{% url 'physical_invoice_unapprove' pi.pk %}" class="status-action-form"'''
FT_NEW = '''    {% elif pi.status == 'approved' %}
      <form method="post" action="{% url 'customer_invoice_send' pi.pk %}" class="status-action-form"
            onsubmit="return confirm('Send this invoice now? It will be numbered and e-mailed to the customer.');">
        {% csrf_token %}
        <input type="hidden" name="next" value="{% url 'customer_invoice_edit' pi.pk %}">
        <button type="submit" class="btn btn-send">
          <i class="fas fa-paper-plane"></i> Send now
        </button>
      </form>
      <form method="post" action="{% url 'physical_invoice_unapprove' pi.pk %}" class="status-action-form"'''

# ----------------------------------------------------- form template: btn-send CSS
FT_CSS_OLD = ".btn-unapprove:hover { background-color: #e8690b; border-color: #d9610a; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }"
FT_CSS_NEW = (".btn-unapprove:hover { background-color: #e8690b; border-color: #d9610a; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }\n"
              ".btn-send { background-color: #007bff; color: white; border: 1px solid #007bff; border-radius: 6px; font-weight: 500; padding: 8px 18px; transition: all 0.2s ease; }\n"
              ".btn-send:hover { background-color: #0069d9; border-color: #0062cc; color: white; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }")


def _load(path):
    if not os.path.exists(path):
        return None
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def main():
    targets = {
        VIEWS: [(V_I1_OLD, V_I1_NEW), (V_I2_OLD, V_I2_NEW), (V_I3_OLD, V_I3_NEW),
                (V_ALL_OLD, V_ALL_NEW), (V_ROW_OLD, V_ROW_NEW),
                (V_APPEND_ANCHOR, V_APPEND_ANCHOR + V_NEW)],
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