# -*- coding: utf-8 -*-
"""
Apply: wire the Physical Invoices help modal into the list screen.

  pages/templates/physical_invoice_list.html
    + {% load help_modal_tags %}        (after {% load static %})
    + a Help button as the first item in the .page-action-buttons row
    + {% render_help_modal "physical_invoices" %}   (before the PDF-viewer include)

This matches how every other module wires Help: the button lives on the main
list screen and opens #physical_invoicesHelpModal. The sub-forms (customer
create/edit, tenant edit) are intentionally not given their own buttons.

REMINDER: the help CONTENT is module-cached -- after adding the section, RESTART
Django so the modal renders. (This template change itself just needs the normal
page reload once the server has the content.)

Fail-loud: each of the three anchors must appear exactly once or nothing is
written.

Run from the repo root:  python apply_help_pi_wiring.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "physical_invoice_list.html")

# 1) load the help tag library
LOAD_OLD = "{% extends 'base.html' %}\n{% load static %}\n"
LOAD_NEW = "{% extends 'base.html' %}\n{% load static %}\n{% load help_modal_tags %}\n"

# 2) Help button as the first child of the action row
BTN_OLD = '''    <div class="page-action-buttons">
      {% if perms.auth.can_edit_tenants %}'''
BTN_NEW = '''    <div class="page-action-buttons">
      <button type="button" class="btn btn-info action-secondary" data-toggle="modal" data-target="#physical_invoicesHelpModal">
        <i class="fas fa-question-circle"></i> Help
      </button>
      {% if perms.auth.can_edit_tenants %}'''

# 3) render the modal just before the PDF viewer include
MODAL_OLD = "{% include 'components/pdf_viewer.html' %}"
MODAL_NEW = "{% render_help_modal \"physical_invoices\" %}\n\n{% include 'components/pdf_viewer.html' %}"

EDITS = [("load tag", LOAD_OLD, LOAD_NEW),
         ("help button", BTN_OLD, BTN_NEW),
         ("render modal", MODAL_OLD, MODAL_NEW)]


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
        src = fh.read()

    if "physical_invoicesHelpModal" in src or "render_help_modal" in src:
        sys.exit("ABORTED - help wiring already present in %s" % TPL)

    problems = []
    for name, old, _new in EDITS:
        c = src.count(old)
        if c != 1:
            problems.append("  %s: anchor found %d time(s) (expected 1)" % (name, c))
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    new_src = src
    for _name, old, new in EDITS:
        new_src = new_src.replace(old, new, 1)

    with io.open(TPL + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (TPL, TPL))
    print("done. next: python manage.py check  (then RESTART Django for the help content)")


if __name__ == "__main__":
    main()