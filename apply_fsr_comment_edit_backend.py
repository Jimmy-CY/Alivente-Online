"""
Apply (step 3a): the comment-edit commit view + context + URL.

Backend for comment editing. Wired but not reachable until 3b adds the modal.

pages/views/issues.py
  1. fsr_comment_edit_commit(request): edits a comment's text with two hard
     guards --
       - Author-only: the editor's initials (first_name[:1]+last_name[:1], the
         same formula fsr_comment_add uses) must equal issues_details_user.
         No superuser bypass.
       - Notify-lock: if issues_details_last_notified_at is set, the comment
         has been sent and can no longer be edited.
     Empty rejected, 255 cap, no-op detected. Save + IssueAuditLog row (with
     the comment FK set, field 'issues_details_comment') run atomically.
  2. fsr_details context gains user_initials (for the author check in the
     template) and edited_comment_ids (comment ids that have an edit audit row,
     for the "(edited)" tag). Both are used by 3b; harmless until then.

pages/urls.py
  3. Route for fsr_comment_edit_commit (id travels in POST, not the URL, since
     3b uses one shared modal for all comments).

Atomic across both files; .py output ast-parsed; endings preserved per file.

Run from the repo root:  python apply_fsr_comment_edit_backend.py
"""
import ast
import os
import sys

ISSUES = os.path.join("pages", "views", "issues.py")
URLS = os.path.join("pages", "urls.py")

# --- 1: new view, inserted before fsr_pdf ---
VIEW_OLD = '''@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def fsr_pdf(request):'''

VIEW_NEW = '''@login_required
@permission_required('auth.can_edit_issues', raise_exception=True)
@require_POST
def fsr_comment_edit_commit(request):
    """Edit a comment's text, author-only and only while it has never been
    notified, writing an IssueAuditLog row (comment FK set) for the change.

    Guards:
      - Author-only: the editor's initials (first_name[:1]+last_name[:1], the
        same formula fsr_comment_add uses) must match issues_details_user. Not
        even a superuser may edit someone else's comment.
      - Notify-lock: once issues_details_last_notified_at is set, the comment
        has been sent via "Notify Now" and can no longer be edited -- it lives
        in someone's inbox and the record must stay truthful.
    """
    comment_id = request.POST.get('comment_id')
    comment = get_object_or_404(issues_details, pk=comment_id)
    issue = comment.issues

    from_param = request.POST.get('from', 'fsr')
    detail_url = reverse('fsr_details', args=[issue.issues_id]) + f"?from={from_param}"

    # Author-only (initials); no superuser bypass.
    editor_initials = ''
    if request.user.is_authenticated:
        editor_initials = f"{request.user.first_name[:1]}{request.user.last_name[:1]}"
    if not editor_initials or comment.issues_details_user != editor_initials:
        messages.error(request, "You can only edit your own comments.")
        return redirect(detail_url)

    # Notify-lock: a comment that has been sent cannot be edited.
    if comment.issues_details_last_notified_at is not None:
        messages.error(request, "This comment has already been sent and can no longer be edited.")
        return redirect(detail_url)

    new_text = (request.POST.get('issues_details_comment') or '').strip()
    if not new_text:
        messages.error(request, "Comment cannot be empty.")
        return redirect(detail_url)
    if len(new_text) > 255:
        messages.error(request, "Comment must be 255 characters or fewer.")
        return redirect(detail_url)

    old_text = comment.issues_details_comment or ''
    if new_text == old_text:
        messages.info(request, "No changes were made.")
        return redirect(detail_url)

    user = request.user if request.user.is_authenticated else None
    try:
        with transaction.atomic():
            comment.issues_details_comment = new_text
            comment.save(update_fields=['issues_details_comment'])
            IssueAuditLog.objects.create(
                issue=issue,
                comment=comment,
                user=user,
                field_name='issues_details_comment',
                old_value=old_text,
                new_value=new_text,
            )
    except Exception as exc:
        messages.error(request, f"Could not save changes: {exc}")
        return redirect(detail_url)

    messages.success(request, "Comment updated.")
    return redirect(detail_url)


@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def fsr_pdf(request):'''

# --- 2: context additions ---
CTX_OLD = '''    context = {
        "props": results,
        "issues": isresults,
        "issues_details": idresults,
        "redirect_url": redirect_url,
        "audit_log": IssueAuditLog.objects.filter(
            issue_id=issues_id
        ).select_related('user'),
    }'''
CTX_NEW = '''    user_initials = ''
    if request.user.is_authenticated:
        user_initials = f"{request.user.first_name[:1]}{request.user.last_name[:1]}"
    edited_comment_ids = set(
        IssueAuditLog.objects.filter(
            issue_id=issues_id,
            field_name='issues_details_comment',
            comment__isnull=False,
        ).values_list('comment_id', flat=True)
    )

    context = {
        "props": results,
        "issues": isresults,
        "issues_details": idresults,
        "redirect_url": redirect_url,
        "audit_log": IssueAuditLog.objects.filter(
            issue_id=issues_id
        ).select_related('user'),
        "user_initials": user_initials,
        "edited_comment_ids": edited_comment_ids,
    }'''

# --- 3: URL ---
URL_OLD = "    path('fsr_edit_commit/<issues_id>', views.fsr_edit_commit, name='fsr_edit_commit'),"
URL_NEW = ("    path('fsr_edit_commit/<issues_id>', views.fsr_edit_commit, name='fsr_edit_commit'),\n"
           "    path('fsr_comment_edit_commit/', views.fsr_comment_edit_commit, name='fsr_comment_edit_commit'),")

EDITS = {
    ISSUES: [(VIEW_OLD, VIEW_NEW), (CTX_OLD, CTX_NEW)],
    URLS: [(URL_OLD, URL_NEW)],
}


def load(path):
    if not os.path.isfile(path):
        sys.exit(f"ABORT: {path} not found (run from repo root).")
    with open(path, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()
    return raw, ("\r\n" in raw), raw.replace("\r\n", "\n")


def main():
    staged = {}
    problems = []
    for path, edits in EDITS.items():
        raw, crlf, norm = load(path)
        for old, new in edits:
            c = norm.count(old)
            if c != 1:
                problems.append(f"[{path}] anchor found {c}x (expected 1): {old[:50]!r}...")
            if new in norm:
                problems.append(f"[{path}] replacement already present: {new[:50]!r}...")
        out = norm
        for old, new in edits:
            out = out.replace(old, new)
        if path.endswith(".py"):
            try:
                ast.parse(out)
            except SyntaxError as e:
                problems.append(f"[{path}] result would not parse: {e}")
        staged[path] = (out, crlf, raw)

    if problems:
        print("ABORT -- nothing written:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    for path, (out, crlf, raw) in staged.items():
        final = out.replace("\n", "\r\n") if crlf else out
        with open(path + ".prebak", "w", encoding="utf-8", newline="") as fh:
            fh.write(raw)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(final)
        print(f"OK: {path} updated.  Endings: {'CRLF' if crlf else 'LF'} preserved.  Backup: {path}.prebak")

    print("Next: python manage.py check ; then step 3b (comment edit control + modal on fsr_details.html).")


if __name__ == "__main__":
    main()