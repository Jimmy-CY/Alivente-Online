# -*- coding: utf-8 -*-
"""
Option B - Step 4a: detach Physical Invoices from the Tenants screen.

  pages/templates/tenant.html
    - remove the desktop "Physical Invoices" secondary button
    - remove the "Physical Invoices" item from the mobile More menu

  pages/templates/physical_invoice_list.html
    - repoint the list's Back button from {% url 'tenant' %} -> {% url 'invoices' %}
      (its new home is the Open Invoices screen)

Step 4b (separate) ADDS the Physical Invoices entry button onto invoices.html.
Apply 4a and 4b together before deploying so the section keeps a UI entry point.

Fail-loud: every anchor must appear exactly once across the two files or nothing
is written.

Run from the repo root:  python apply_pi_perms_step4a_move_button.py
"""
import io
import os
import sys

TENANT = os.path.join("pages", "templates", "tenant.html")
PILIST = os.path.join("pages", "templates", "physical_invoice_list.html")

# --- tenant.html: desktop secondary button (removed, incl. its line break) ---
TEN_DESKTOP = (
    "      <a href=\"{% url 'physical_invoice_list' %}\" class=\"btn btn-info action-secondary\">Physical Invoices</a>\n"
)

# --- tenant.html: More-menu item (removed, incl. its line break) ---
TEN_MORE = (
    "          <a href=\"{% url 'physical_invoice_list' %}\" class=\"action-more-item\" role=\"menuitem\">\n"
    "            <i class=\"fas fa-file-invoice\"></i> Physical Invoices\n"
    "          </a>\n"
)

# --- physical_invoice_list.html: Back button repoint ---
PI_BACK_OLD = "<a href=\"{% url 'tenant' %}\" class=\"btn btn-info action-back\" aria-label=\"Back to tenants\">"
PI_BACK_NEW = "<a href=\"{% url 'invoices' %}\" class=\"btn btn-info action-back\" aria-label=\"Back to invoices\">"


def _read(path):
    if not os.path.exists(path):
        sys.exit("ABORTED - missing file: %s" % path)
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def main():
    tsrc = _read(TENANT)
    psrc = _read(PILIST)

    problems = []
    for label, src, anchor in [
        ("tenant.html desktop button", tsrc, TEN_DESKTOP),
        ("tenant.html More-menu item", tsrc, TEN_MORE),
        ("physical_invoice_list.html Back", psrc, PI_BACK_OLD),
    ]:
        c = src.count(anchor)
        if c != 1:
            problems.append("  %s: anchor found %d time(s) (expected 1)" % (label, c))

    # Guard against re-runs.
    if "Back to invoices" in psrc:
        problems.append("  physical_invoice_list.html already points Back at invoices")

    if problems:
        sys.exit("ABORTED - nothing written:\n" + "\n".join(problems))

    tnew = tsrc.replace(TEN_DESKTOP, "", 1).replace(TEN_MORE, "", 1)
    pnew = psrc.replace(PI_BACK_OLD, PI_BACK_NEW, 1)

    # Physical Invoices must be fully gone from the tenant screen.
    if "physical_invoice_list" in tnew:
        sys.exit("ABORTED - a physical_invoice_list reference still remains in tenant.html; nothing written.")

    with io.open(TENANT + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(tsrc)
    with io.open(TENANT, "w", encoding="utf-8", newline="") as fh:
        fh.write(tnew)
    with io.open(PILIST + ".prebak4a", "w", encoding="utf-8", newline="") as fh:
        fh.write(psrc)
    with io.open(PILIST, "w", encoding="utf-8", newline="") as fh:
        fh.write(pnew)

    print("OK: %s  (removed desktop button + More-menu item, backup .prebak)" % TENANT)
    print("OK: %s  (Back -> invoices, backup .prebak4a)" % PILIST)
    print("done. Step 4b adds the entry button to the Open Invoices screen.")


if __name__ == "__main__":
    main()