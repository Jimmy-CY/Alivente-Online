"""
Apply: add client_email_body to PhysicalInvoiceProfile.

  pages/models.py
    add a client_email_body TextField (blank) to PhysicalInvoiceProfile,
    immediately after billing_tel (i.e. at the end of the customer block,
    before the water-cycle fields).

The field stores the saved greeting + body for the monthly invoice e-mail.
{month} is the one substitution token -> "<Month> <Year>" (e.g. "June 2026"),
filled in by the send cron. Blank means the cron uses a generic default.

Fail-loud: the anchor must appear exactly once or nothing is written.
After running:  python manage.py makemigrations pages
                python manage.py migrate
                python manage.py check

Run from the repo root:  python apply_client_email_body.py
"""
import ast
import io
import os
import sys

MODELS = os.path.join("pages", "models.py")

MODELS_EDITS = [
    ("""    billing_tel = models.CharField(max_length=64, blank=True,
        help_text="Defaults to the tenant contact number if blank.")""",
     """    billing_tel = models.CharField(max_length=64, blank=True,
        help_text="Defaults to the tenant contact number if blank.")
    client_email_body = models.TextField(blank=True,
        help_text="Saved greeting and body for the monthly invoice e-mail. "
                  "Use {month} where the period should appear; the send cron "
                  "replaces it with the month and year (e.g. 'June 2026'). "
                  "Leave blank to use a generic default.")"""),
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
    src, problems = _verify(MODELS, MODELS_EDITS)
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    new_src = src
    for old, new in MODELS_EDITS:
        new_src = new_src.replace(old, new, 1)
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        sys.exit("ABORTED - %s does not parse: %s" % (MODELS, e))

    with io.open(MODELS + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(MODELS, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (MODELS, MODELS))
    print("done. next: makemigrations pages, migrate, check")


if __name__ == "__main__":
    main()