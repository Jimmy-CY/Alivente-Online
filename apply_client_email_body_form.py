# -*- coding: utf-8 -*-
"""
Apply: Client Email Body textarea on the tenant add + edit forms (step 3).

  pages/templates/tenant_add.html
    insert a "Client Email Body" textarea (bound to form_data.client_email_body)
    directly under the Billing Address row.

  pages/templates/tenant_edit.html
    same, bound to tresults.physical_invoice_profile.client_email_body.

The {month} token in the hint/placeholder is literal text (single braces), not a
Django variable, so it passes through untouched.

Fail-loud: every anchor must appear exactly once or nothing is written.
Templates need no migration or restart; a browser refresh shows them.

Run from the repo root:  python apply_client_email_body_form.py
"""
import io
import os
import sys

ADD = os.path.join("pages", "templates", "tenant_add.html")
EDIT = os.path.join("pages", "templates", "tenant_edit.html")

HINT = ('<small class="form-text text-muted">The greeting and body of the monthly '
        'invoice e-mail. Type <code>{month}</code> where the period should appear '
        '&mdash; it becomes e.g. &ldquo;June 2026&rdquo; when sent. The signature and '
        'contact footer are added automatically. Leave blank to use a generic message.'
        '</small>')

PLACEHOLDER = "Dear ...,&#10;&#10;Please find attached the rental invoice for {month}."


def _new_row(bound_value):
    return (
        '\n\n    <div class="form-row">\n'
        '      <div class="col-md-12">\n'
        '        <div class="form-group">\n'
        '          <label for="client_email_body"><strong>Client Email Body</strong></label>\n'
        '          <textarea class="form-control" id="client_email_body" name="client_email_body" rows="5"\n'
        '                    placeholder="%s">%s</textarea>\n'
        '          %s\n'
        '        </div>\n'
        '      </div>\n'
        '    </div>' % (PLACEHOLDER, bound_value, HINT)
    )


ADD_ANCHOR = ('                    placeholder="Customer address &mdash; one line per row">'
              '{{ form_data.billing_address }}</textarea>\n'
              '        </div>\n'
              '      </div>\n'
              '    </div>')

EDIT_ANCHOR = ('                    placeholder="Customer address &mdash; one line per row">'
               '{{ tresults.physical_invoice_profile.billing_address }}</textarea>\n'
               '        </div>\n'
               '      </div>\n'
               '    </div>')

ADD_EDITS = [(ADD_ANCHOR, ADD_ANCHOR + _new_row("{{ form_data.client_email_body }}"))]
EDIT_EDITS = [(EDIT_ANCHOR, EDIT_ANCHOR + _new_row("{{ tresults.physical_invoice_profile.client_email_body }}"))]


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
    targets = [(ADD, ADD_EDITS), (EDIT, EDIT_EDITS)]

    loaded, all_problems = [], []
    for path, edits in targets:
        src, problems = _verify(path, edits)
        all_problems.extend(problems)
        loaded.append((path, edits, src))
    if all_problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(all_problems))

    for path, edits, src in loaded:
        new_src = src
        for old, new in edits:
            new_src = new_src.replace(old, new, 1)
        with io.open(path + ".prebak", "w", encoding="utf-8", newline="") as fh:
            fh.write(src)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_src)
        print("OK: %s (backup %s.prebak)" % (path, path))

    print("done. refresh the tenant add/edit pages to see the field.")


if __name__ == "__main__":
    main()