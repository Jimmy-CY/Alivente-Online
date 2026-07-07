"""
Apply (step 3b): comment edit control + modal on fsr_details.html.

Six edits, all in the template:
  1. "(edited)" tag after a comment's text, shown when the comment id is in
     edited_comment_ids (from 3a).
  2. An Edit pencil on each comment, shown ONLY when it is the viewer's own
     comment (issues_details_user == user_initials) AND it has not been
     notified (issues_details_last_notified_at is empty) -- the author +
     notify-lock rule, evaluated in-template to mirror the view's guards.
  3. A shared Edit Comment modal (same ei-modal styling), populated from the
     clicked comment's data- attributes, posting to fsr_comment_edit_commit.
  4. History label map extended: comment edits read "changed Comment" instead
     of the raw field name.
  5. CSS for the edit button / edited tag / note.
  6. Vanilla-JS open/close/populate for the comment modal.

Fail-loud (every anchor exactly once) and CRLF preserved.

Run from the repo root:  python apply_fsr_comment_edit_ui.py
"""
import os
import sys

PATH = os.path.join("pages", "templates", "fsr_details.html")

# 1: (edited) tag
TAG_OLD = '''                                            <span class="comment-text">{{ idresults.issues_details_comment }}</span>'''
TAG_NEW = '''                                            <span class="comment-text">{{ idresults.issues_details_comment }}</span>
                                            {% if idresults.issues_details_id in edited_comment_ids %}<span class="comment-edited-tag">(edited)</span>{% endif %}'''

# 2: Edit pencil (author-only + not-notified), before the notify cell
BTN_OLD = '''                                        <span class="notify-urgent-cell" data-comment-id="{{ idresults.issues_details_id }}">'''
BTN_NEW = '''                                        {% if idresults.issues_details_user == user_initials and not idresults.issues_details_last_notified_at %}
                                        <button type="button" class="comment-edit-btn"
                                                data-comment-id="{{ idresults.issues_details_id }}"
                                                data-comment-text="{{ idresults.issues_details_comment|default:'' }}"
                                                onclick="openEditCommentModal(this)"
                                                title="Edit your comment">
                                            <i class="fas fa-pencil-alt"></i> Edit
                                        </button>
                                        {% endif %}
                                        <span class="notify-urgent-cell" data-comment-id="{{ idresults.issues_details_id }}">'''

# 3: History label map -> add Comment
HIST_OLD = '''                                {% if entry.field_name == 'issues_heading' %}Heading{% elif entry.field_name == 'issues_description' %}Description{% elif entry.field_name == 'prop' %}Property{% else %}{{ entry.field_name }}{% endif %}'''
HIST_NEW = '''                                {% if entry.field_name == 'issues_heading' %}Heading{% elif entry.field_name == 'issues_description' %}Description{% elif entry.field_name == 'prop' %}Property{% elif entry.field_name == 'issues_details_comment' %}Comment{% else %}{{ entry.field_name }}{% endif %}'''

# 4: comment modal, before the updateStatus script
MODAL_OLD = '''            <script>
            function updateStatus(issueId, newStatus) {'''
MODAL_NEW = '''            {% if perms.auth.can_edit_issues %}
            <div id="editCommentModal" class="ei-modal">
                <div class="ei-modal-dialog">
                    <div class="ei-modal-content">
                        <div class="ei-modal-header">
                            <h2>Edit Comment</h2>
                            <button type="button" class="ei-modal-close" onclick="closeEditCommentModal()">&times;</button>
                        </div>
                        <form method="post" action="{% url 'fsr_comment_edit_commit' %}">
                            {% csrf_token %}
                            <input type="hidden" name="from" value="{{ request.GET.from|default:'fsr' }}">
                            <input type="hidden" name="comment_id" id="ec_comment_id" value="">
                            <div class="ei-modal-body">
                                <label class="ei-label" for="ec_text">Comment</label>
                                <textarea id="ec_text" name="issues_details_comment" class="ei-input" rows="4" maxlength="255" required></textarea>
                                <p class="ec-note">You can edit only your own comments, and only until they&rsquo;ve been sent via &ldquo;Notify Now&rdquo;.</p>
                            </div>
                            <div class="ei-modal-footer">
                                <button type="button" class="btn btn-secondary" onclick="closeEditCommentModal()">Cancel</button>
                                <button type="submit" class="btn btn-info">Save Comment</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            {% endif %}

            <script>
            function updateStatus(issueId, newStatus) {'''

# 5: CSS, before </style>
CSS_OLD = "</style>"
CSS_NEW = '''/* ===== Comment edit (added) ===== */
.comment-edit-btn { background: #e9ecef; border: 1px solid #ced4da; color: #495057; padding: 4px 9px; border-radius: 3px; font-size: 12px; cursor: pointer; white-space: nowrap; }
.comment-edit-btn:hover { background: #dde2e6; }
.comment-edited-tag { color: #6c757d; font-style: italic; font-size: 12px; margin-left: 6px; }
.ec-note { color: #6c757d; font-size: 12px; margin: 10px 0 0; }
</style>'''

# 6: comment modal JS, before {% endblock %}
JS_OLD = '''</script>
{% endblock %}'''
JS_NEW = '''</script>

<script>
// Edit Comment modal controls (self-contained; not Bootstrap)
function openEditCommentModal(btn) {
    var id = btn.getAttribute('data-comment-id');
    var text = btn.getAttribute('data-comment-text') || '';
    var idEl = document.getElementById('ec_comment_id');
    var textEl = document.getElementById('ec_text');
    if (idEl) idEl.value = id;
    if (textEl) textEl.value = text;
    var m = document.getElementById('editCommentModal');
    if (m) m.classList.add('show');
}
function closeEditCommentModal() {
    var m = document.getElementById('editCommentModal');
    if (m) m.classList.remove('show');
}
document.addEventListener('click', function(e) {
    var m = document.getElementById('editCommentModal');
    if (m && e.target === m) closeEditCommentModal();
});
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeEditCommentModal();
});
</script>
{% endblock %}'''

EDITS = [
    (TAG_OLD, TAG_NEW),
    (BTN_OLD, BTN_NEW),
    (HIST_OLD, HIST_NEW),
    (MODAL_OLD, MODAL_NEW),
    (CSS_OLD, CSS_NEW),
    (JS_OLD, JS_NEW),
]


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
    if crlf:
        out = out.replace("\n", "\r\n")

    with open(PATH + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(raw)
    with open(PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)

    print(f"OK: {PATH} updated (comment edit UI).  Endings: {'CRLF' if crlf else 'LF'} preserved.")
    print(f"Backup: {PATH}.prebak")
    print("Next: python manage.py check ; hard-refresh an issue with your own un-notified comment.")


if __name__ == "__main__":
    main()