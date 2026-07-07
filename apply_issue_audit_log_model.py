"""
Apply (step 2a): add the IssueAuditLog model to pages/models.py.

Field-level change history for an issue. One row per changed field per edit;
the edit view (step 2b) captures a before-snapshot, diffs it against the
submitted values, and writes a row only for fields that actually changed.
Rendered as the History section (step 2c), and the substrate a later
edit-notification email can read from.

Design notes baked into the model:
  - Not workspace-scoped. Issues are property-management records with no
    workspace FK, so their history is unscoped too (FK to issues + User).
  - user is SET_NULL so history survives a user-account deletion.
  - A nullable `comment` FK is included now so the (later) comment-editing
    step shares this same table with no second migration; it stays NULL for
    issue-field changes.
  - Property changes will store the property NAME in old/new value (done in
    the view), not the pk, for readable history.

Inserts the class between issues_details and prop_values. One fail-loud edit
(anchor must appear exactly once), ast-parsed before writing, CRLF preserved.

After running:  python manage.py makemigrations pages ; python manage.py migrate

Run from the repo root:  python apply_issue_audit_log_model.py
"""
import ast
import os
import sys

PATH = os.path.join("pages", "models.py")

OLD = '''    class Meta:
        db_table="issues_details"

class prop_values(models.Model):'''

NEW = '''    class Meta:
        db_table="issues_details"

class IssueAuditLog(models.Model):
    """Field-level change history for an issue (and, later, its comments).

    One row per changed field per edit: editing the heading and the property
    in a single save writes two rows. The issue-edit view captures a
    before-snapshot, diffs it against the submitted values, and writes a row
    only for fields that actually changed. Rendered as the History section on
    the issue detail page, and the substrate a later edit-notification email
    reads from.

    Not workspace-scoped: issues are property-management records with no
    workspace FK, so their history follows the same unscoped pattern.
    Property changes store the property NAME in old_value/new_value for
    readability, not the pk. The `comment` FK stays NULL for issue-field
    changes; it is populated by the (later) comment-editing step, which shares
    this same log.
    """
    issue = models.ForeignKey(
        issues,
        on_delete=models.CASCADE,
        related_name='audit_log',
    )
    comment = models.ForeignKey(
        issues_details,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='audit_log',
        help_text='Set when the change was to a comment rather than an issue '
                  'field; NULL for issue-field changes.',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='issue_edits',
        help_text='Who made the change. NULL if the account was later removed.',
    )
    field_name = models.CharField(
        max_length=50,
        help_text="Model field that changed, e.g. 'issues_heading', "
                  "'issues_description', 'prop'.",
    )
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'issue_audit_log'
        verbose_name = 'Issue Audit Log Entry'
        verbose_name_plural = 'Issue Audit Log'
        ordering = ['-changed_at', '-id']

    def __str__(self):
        who = self.user.username if self.user else 'unknown'
        return f"{self.field_name} on issue {self.issue_id} by {who}"

class prop_values(models.Model):'''

EDITS = [(OLD, NEW)]


def main():
    if not os.path.isfile(PATH):
        sys.exit(f"ABORT: {PATH} not found (run from repo root).")

    with open(PATH, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()
    crlf = "\r\n" in raw
    norm = raw.replace("\r\n", "\n")

    problems = []
    for old, new in EDITS:
        c = norm.count(old)
        if c != 1:
            problems.append(f"anchor found {c}x (expected 1): {old[:55]!r}...")
        if new in norm:
            problems.append(f"replacement already present: {new[:55]!r}...")
    if problems:
        print("ABORT -- nothing written:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    out = norm
    for old, new in EDITS:
        out = out.replace(old, new)

    try:
        ast.parse(out)
    except SyntaxError as e:
        sys.exit(f"ABORT: result would not parse ({e}); nothing written.")

    if crlf:
        out = out.replace("\n", "\r\n")

    with open(PATH + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(raw)
    with open(PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)

    print(f"OK: {PATH} updated (IssueAuditLog model added).  "
          f"Endings: {'CRLF' if crlf else 'LF'} preserved.")
    print(f"Backup: {PATH}.prebak")
    print("Next: python manage.py makemigrations pages ; python manage.py migrate")


if __name__ == "__main__":
    main()