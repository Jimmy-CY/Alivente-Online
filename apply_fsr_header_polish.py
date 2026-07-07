"""
Apply (step 3 polish): header layout + live Edit-button removal on notify.

Five fixes, all in pages/templates/fsr_details.html:

  1. When "Notify Now" succeeds (or reports cooldown -- i.e. the comment is now
     notified), also remove that comment's Edit button from the DOM, so the
     notify-lock takes effect immediately without a page refresh.
  2. Move the "Edit Issue" button out of the header into the top action bar,
     to the left of Back. It opens the same modal, so it works from there.
  3. Drop the <br/> under the action bar and tighten margins so the issue
     header sits closer under Back.
  4. Put Date Logged / Property / Status on one line (desktop; they stack again
     on mobile).
  5. Reduce the gap between the header and the Enter-New-Comment box.

Fail-loud (every anchor exactly once) and CRLF preserved.

Run from the repo root:  python apply_fsr_header_polish.py
"""
import os
import sys

PATH = os.path.join("pages", "templates", "fsr_details.html")

# 1: notify handler removes the comment's Edit button when it becomes notified
NOTIFY_OLD = '''            if (res.body.ok) {
                cell.innerHTML = '<span class="notified-badge" style="' + badgeStyle + '">Notified just now</span>';
            } else if (res.body.reason === 'cooldown') {
                cell.innerHTML = '<span class="notified-badge" style="' + badgeStyle + '">Notified ' + res.body.minutes_ago + ' min ago</span>';
            } else if (res.body.reason === 'no_recipients') {'''
NOTIFY_NEW = '''            if (res.body.ok) {
                cell.innerHTML = '<span class="notified-badge" style="' + badgeStyle + '">Notified just now</span>';
                var _eb1 = document.querySelector('.comment-edit-btn[data-comment-id="' + commentId + '"]');
                if (_eb1) _eb1.remove();
            } else if (res.body.reason === 'cooldown') {
                cell.innerHTML = '<span class="notified-badge" style="' + badgeStyle + '">Notified ' + res.body.minutes_ago + ' min ago</span>';
                var _eb2 = document.querySelector('.comment-edit-btn[data-comment-id="' + commentId + '"]');
                if (_eb2) _eb2.remove();
            } else if (res.body.reason === 'no_recipients') {'''

# 2 + 3: Edit Issue into the action bar (left of Back); drop the <br/>
BAR_OLD = '''<div class="page-action-bar">
    <div class="page-action-bar-inner">
        <a href="#" onclick="handleBackButton(); return false;" class="btn btn-info">Back</a>
    </div>
</div>

<br/>

<!-- Issue Details in Friday Status Report Style -->'''
BAR_NEW = '''<div class="page-action-bar">
    <div class="page-action-bar-inner">
        {% if perms.auth.can_edit_issues %}
        <button type="button" class="btn btn-info" onclick="openEditIssueModal()">
            <i class="fas fa-edit"></i> Edit Issue
        </button>
        {% endif %}
        <a href="#" onclick="handleBackButton(); return false;" class="btn btn-info">Back</a>
    </div>
</div>

<!-- Issue Details in Friday Status Report Style -->'''

# 2: remove the Edit Issue button from the header
HDR_OLD = '''                        <h4 class="status-display">Status: {{ isresults.issues_status|upper }}</h4>
                        {% if perms.auth.can_edit_issues %}
                        <button type="button" class="btn btn-info ei-edit-btn" onclick="openEditIssueModal()">
                            <i class="fas fa-edit"></i> Edit Issue
                        </button>
                        {% endif %}
                    </div>'''
HDR_NEW = '''                        <h4 class="status-display">Status: {{ isresults.issues_status|upper }}</h4>
                    </div>'''

# 4 + 5: layout CSS, before </style>
CSS_OLD = "</style>"
CSS_NEW = '''/* ===== Header polish (added) ===== */
.page-action-bar { margin-bottom: 10px; }
.report-container { padding-top: 8px; min-height: auto; }
.issue-header-section { margin-bottom: 12px; padding: 16px 20px; }
.issue-header-section .issue-title { margin-bottom: 6px; }
.status-card { padding-top: 14px; }
.issue-header-section .date-logged-display,
.issue-header-section .property-display,
.issue-header-section .status-display {
    display: inline-block;
    margin: 6px 26px 0 0;
    font-size: 1.05rem;
    vertical-align: baseline;
}
@media (max-width: 768px) {
    .issue-header-section .date-logged-display,
    .issue-header-section .property-display,
    .issue-header-section .status-display {
        display: block;
        margin: 0 0 6px 0;
    }
}
</style>'''

EDITS = [
    (NOTIFY_OLD, NOTIFY_NEW),
    (BAR_OLD, BAR_NEW),
    (HDR_OLD, HDR_NEW),
    (CSS_OLD, CSS_NEW),
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

    print(f"OK: {PATH} updated (header polish + live edit-button removal).  "
          f"Endings: {'CRLF' if crlf else 'LF'} preserved.")
    print(f"Backup: {PATH}.prebak")
    print("Next: python manage.py check ; hard-refresh, check header + notify a comment.")


if __name__ == "__main__":
    main()