"""
Apply: persist client_email_body on PhysicalInvoiceProfile (step 2).

  pages/views/tenants.py
    1. _apply_physical_invoice_fields: read client_email_body from the POST and
       store it on the profile (right after billing_tel).
    2. duplicate_tenant_view: carry client_email_body across when a tenant is
       duplicated for renewal.

Fail-loud: every anchor must appear exactly once or nothing is written.
After running:  python manage.py check

Run from the repo root:  python apply_client_email_body_view.py
"""
import ast
import io
import os
import sys

VIEW = os.path.join("pages", "views", "tenants.py")

VIEW_EDITS = [
    ("""    profile.billing_tel = (request.POST.get('billing_tel') or '').strip()""",
     """    profile.billing_tel = (request.POST.get('billing_tel') or '').strip()
    profile.client_email_body = (request.POST.get('client_email_body') or '').strip()"""),

    ("""                billing_tel=src_profile.billing_tel,""",
     """                billing_tel=src_profile.billing_tel,
                client_email_body=src_profile.client_email_body,"""),
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
    src, problems = _verify(VIEW, VIEW_EDITS)
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    new_src = src
    for old, new in VIEW_EDITS:
        new_src = new_src.replace(old, new, 1)
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        sys.exit("ABORTED - %s does not parse: %s" % (VIEW, e))

    with io.open(VIEW + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(VIEW, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (VIEW, VIEW))
    print("done. next: check")


if __name__ == "__main__":
    main()