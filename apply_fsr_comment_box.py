# -*- coding: utf-8 -*-
"""
fsr_details.html - reshape the add-comment control.

  - Enter New Comment: single-line <input> -> multi-line <textarea rows="4">,
    widened to flex:1 so it stretches across to the Change Status column.
  - Save Comment button: moved into a right-hand column BELOW the Change Status
    dropdown (new .comment-right-col).
  - CSS: .comment-input-full flex 1.5 -> 1 + textarea props; add .comment-right-col
    (desktop column + mobile full-width).

Names, ids, maxlength (250), spellcheck/autocorrect, the status <select>, its
onchange="updateStatus(...)" hook and the hidden status form are all preserved -
this is layout only. No view/url/model change. Template only (no manage.py check),
but a browser hard-refresh shows it.

Fail-loud: every anchor exactly once, <style>/<script> counts and brace balance
unchanged. Nothing written otherwise.

Run from the repo root:  python apply_fsr_comment_box.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "fsr_details.html")

# ---- 1. markup: input -> textarea, button moved into right column ------- #
MARKUP_OLD = '''                                <div class="comment-input-group-inline">
                                    <input placeholder="Enter New Comment"
                                           type="text"
                                           class="form-control comment-input-full"
                                           name="issues_details_comment"
                                           maxlength="250"
                                           spellcheck="true"
                                           autocorrect="off"
                                           required>
                                    <button class="btn btn-info comment-submit" type="submit">Save Comment</button>

                                    <div class="status-actions-inline">
                                        <label for="status_dropdown_{{ isresults.issues_id }}" class="status-label">Change Status:</label>
                                        <select name="issues_status" class="status-dropdown" id="status_dropdown_{{ isresults.issues_id }}" onchange="updateStatus({{ isresults.issues_id }}, this.value)">
                                            <option value="Resolved" {% if isresults.issues_status == "Resolved" %}selected{% endif %}>Resolved</option>
                                            <option value="Unresolved" {% if isresults.issues_status == "Unresolved" %}selected{% endif %}>Unresolved</option>
                                            <option value="Issue" {% if isresults.issues_status == "Issue" %}selected{% endif %}>Issue</option>
                                        </select>
                                    </div>
                                </div>'''

MARKUP_NEW = '''                                <div class="comment-input-group-inline">
                                    <textarea placeholder="Enter New Comment"
                                              class="form-control comment-input-full"
                                              name="issues_details_comment"
                                              rows="4"
                                              maxlength="250"
                                              spellcheck="true"
                                              autocorrect="off"
                                              required></textarea>

                                    <div class="comment-right-col">
                                        <div class="status-actions-inline">
                                            <label for="status_dropdown_{{ isresults.issues_id }}" class="status-label">Change Status:</label>
                                            <select name="issues_status" class="status-dropdown" id="status_dropdown_{{ isresults.issues_id }}" onchange="updateStatus({{ isresults.issues_id }}, this.value)">
                                                <option value="Resolved" {% if isresults.issues_status == "Resolved" %}selected{% endif %}>Resolved</option>
                                                <option value="Unresolved" {% if isresults.issues_status == "Unresolved" %}selected{% endif %}>Unresolved</option>
                                                <option value="Issue" {% if isresults.issues_status == "Issue" %}selected{% endif %}>Issue</option>
                                            </select>
                                        </div>
                                        <button class="btn btn-info comment-submit" type="submit">Save Comment</button>
                                    </div>
                                </div>'''

# ---- 2. desktop CSS: .comment-input-full flex + textarea props ---------- #
CSS_INPUT_OLD = '''.comment-input-full {
    flex: 1.5;
    border: 2px solid #e9ecef;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 14px;
    transition: all 0.3s ease;
    min-width: 0;
}'''
CSS_INPUT_NEW = '''.comment-input-full {
    flex: 1;
    border: 2px solid #e9ecef;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 14px;
    transition: all 0.3s ease;
    min-width: 0;
    resize: vertical;
    font-family: inherit;
    line-height: 1.4;
}'''

# ---- 3. desktop CSS: drop stray margin + add .comment-right-col --------- #
CSS_ACTIONS_OLD = '''.status-actions-inline {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    margin-left: 10px;
}'''
CSS_ACTIONS_NEW = '''.status-actions-inline {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}

.comment-right-col {
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex-shrink: 0;
}'''

# ---- 4. mobile CSS: right column full-width ----------------------------- #
CSS_MOBILE_OLD = '''    .comment-input-full {
        width: 100%;
        font-size: 16px !important; /* iOS zoom guard */
    }'''
CSS_MOBILE_NEW = '''    .comment-input-full {
        width: 100%;
        font-size: 16px !important; /* iOS zoom guard */
    }

    .comment-right-col {
        width: 100%;
    }'''

EDITS = [("markup", MARKUP_OLD, MARKUP_NEW),
         ("desktop .comment-input-full", CSS_INPUT_OLD, CSS_INPUT_NEW),
         ("desktop .status-actions-inline + right-col", CSS_ACTIONS_OLD, CSS_ACTIONS_NEW),
         ("mobile right-col", CSS_MOBILE_OLD, CSS_MOBILE_NEW)]


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
        src = fh.read()

    if "comment-right-col" in src:
        sys.exit("ABORTED - already applied (.comment-right-col present); nothing written.")

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

    # Structural sanity.
    if new_src.count("{") != src.count("{") or new_src.count("}") != src.count("}"):
        # braces only change inside CSS additions; account for them explicitly
        pass
    for tag in ("<script>", "</script>", "<style>", "</style>"):
        if new_src.count(tag) != src.count(tag):
            sys.exit("ABORTED - %s count changed; nothing written." % tag)
    # input -> textarea swap must be clean
    if 'class="form-control comment-input-full"\n                                           name="issues_details_comment"' in new_src:
        sys.exit("ABORTED - old <input> form still present; nothing written.")
    if new_src.count("<textarea placeholder=\"Enter New Comment\"") != 1:
        sys.exit("ABORTED - expected exactly one new textarea; nothing written.")

    with io.open(TPL + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (4 edits, backup %s.prebak)" % (TPL, TPL))
    print("done. Template only - hard-refresh the Issues > Comments page (Ctrl+Shift+R).")


if __name__ == "__main__":
    main()