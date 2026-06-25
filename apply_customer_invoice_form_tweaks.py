# -*- coding: utf-8 -*-
"""
Apply: two refinements to the customer-invoice form.

  pages/templates/customer_invoice_form.html
    1. "Save as a new customer" checkbox is greyed (disabled) and unticked
       whenever a saved customer is picked; re-enabled when the dropdown goes
       back to "New / one-off". Applied on change AND on page load (so an edit
       screen that opens with a linked customer shows it greyed from the start).
    2. New blank "Add Line" rows default the VAT dropdown to "Yes" (existing
       saved lines still reflect their own stored vatable).

Single-file, surgical. No view/route/migration changes.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check  (template-only, but confirms no breakage)

Run from the repo root:  python apply_customer_invoice_form_tweaks.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "customer_invoice_form.html")

EDITS = [
    # 1) Add-Line template row: default VAT to Yes.
    ('''    <td>
      <select name="line_vatable" class="form-control line-input line-vat">
        <option value="1">Yes</option>
        <option value="0" selected>No</option>
      </select>
    </td>''',
     '''    <td>
      <select name="line_vatable" class="form-control line-input line-vat">
        <option value="1" selected>Yes</option>
        <option value="0">No</option>
      </select>
    </td>'''),

    # 2) JS: disable/untick "save as new" when a customer is picked; init on load.
    ('''  sel.addEventListener('change', function () {
    var opt = sel.options[sel.selectedIndex];
    if (!opt || !opt.value) return;  // "new / one-off" — leave fields as typed
    var map = {
      bill_name: 'name', bill_customer_label: 'label', bill_address: 'address',
      bill_tel: 'tel', bill_email_to: 'emailto', bill_email_cc: 'emailcc', bill_email_body: 'emailbody'
    };
    Object.keys(map).forEach(function (fieldId) {
      var el = document.getElementById(fieldId);
      if (el) el.value = opt.getAttribute('data-' + map[fieldId]) || '';
    });
    // Picking an existing customer makes "save as new" irrelevant.
    var sc = document.getElementById('saveCustomer');
    if (sc) sc.checked = false;
  });''',
     '''  function syncSaveNewState() {
    var sc = document.getElementById('saveCustomer');
    if (!sc) return;
    var picked = !!sel.value;  // a real saved customer is selected
    if (picked) { sc.checked = false; sc.disabled = true; }
    else { sc.disabled = false; }
  }

  sel.addEventListener('change', function () {
    var opt = sel.options[sel.selectedIndex];
    if (opt && opt.value) {
      var map = {
        bill_name: 'name', bill_customer_label: 'label', bill_address: 'address',
        bill_tel: 'tel', bill_email_to: 'emailto', bill_email_cc: 'emailcc', bill_email_body: 'emailbody'
      };
      Object.keys(map).forEach(function (fieldId) {
        var el = document.getElementById(fieldId);
        if (el) el.value = opt.getAttribute('data-' + map[fieldId]) || '';
      });
    }
    // Grey out / untick "save as new" whenever a saved customer is picked.
    syncSaveNewState();
  });

  // Reflect the correct state on initial load (e.g. edit screen with a linked customer).
  syncSaveNewState();'''),

    # 3) Dim the whole "Save as a new customer" control when its checkbox is disabled.
    (".save-new-label input { width: 16px; height: 16px; }",
     ".save-new-label input { width: 16px; height: 16px; }\n"
     ".save-new-label input:disabled { cursor: not-allowed; }\n"
     ".save-new-group:has(input:disabled) { opacity: 0.5; }\n"
     ".save-new-group:has(input:disabled) .save-new-label { cursor: not-allowed; }"),
]


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
        src = fh.read()

    problems = []
    for i, (old, _new) in enumerate(EDITS, 1):
        n = src.count(old)
        if n != 1:
            problems.append("  edit %d: anchor found %d time(s) (expected 1)" % (i, n))
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    new_src = src
    for old, new in EDITS:
        new_src = new_src.replace(old, new, 1)

    with io.open(TPL + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (TPL, TPL))
    print("done. next: python manage.py check")


if __name__ == "__main__":
    main()