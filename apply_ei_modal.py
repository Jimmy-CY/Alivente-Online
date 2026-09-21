# -*- coding: utf-8 -*-
"""apply_ei_modal.py - the Issue page's two edit pop-ups become the house
pop-up: a Bootstrap modal with base's header and base's fields.

    python apply_ei_modal.py --check     dry run, nothing written
    python apply_ei_modal.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

WHAT WAS MEASURED (21 Sep, claude/action_bar_and_ei_survey.md)

  fsr_details.html carries Edit Issue (heading, description, property) and
  Edit Comment (comment and a note) in a dialect of its own: .ei-modal,
  -dialog, -content, -header, -body, -footer, -close, .ei-label and
  .ei-input, with a hand-written script that opens them, and closes them on
  the overlay and on Escape. Every other business pop-up is a Bootstrap
  modal. .ei-input was already .form-control in all but name; .ei-label
  was the bold label. Since the modal-heads round the header's page rule
  has been dead - base's .alv-modal-head wins.

WHAT THIS DOES - agreed 21 Sep ("Fields and shell")

  1. Both pop-ups become .modal.fade > .modal-dialog > .modal-content, with
     .modal-header.alv-modal-head, h5.modal-title, Bootstrap's .close,
     .modal-body and .modal-footer - the shape projects_detail's Update
     Status pop-up has.
  2. Every field becomes .form-group > label > strong (+ .alv-req where
     required) and .form-control; the comment note becomes .form-text.
     Ids, names, values, actions, csrf and hidden inputs are unchanged.
  3. Cancel and the close button carry data-dismiss. The script keeps the
     four function names the page's buttons call, and hands opening and
     closing to Bootstrap - which closes on Escape and on the backdrop, so
     the page's own listeners for those go.
  4. The page's .ei-* rules and .ec-note go, and the phone block that only
     held .ei-* rules.
  5. test_fsr_palette.py pinned the .ei-* rules as live, and
     test_print_queries.py counted fsr_details' phone blocks on the file as
     it is now; both read the file as their own round left it (LATER).
  6. alv_rounds.py learns this round; the suite goes on the push gate; two
     fixture files are added so the suite can run the page's real
     jQuery 3.6.0 and Bootstrap 4.1.3 without the network.

  What a user sees change: the fields are the same size and border. The
  pop-up's footer is white with a rule above it instead of grey, and on a
  phone the pop-up floats with a margin instead of filling the screen -
  exactly as every other business pop-up does.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import ast
import hashlib
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_eimodal'
SUITE = 'test_ei_modal.py'
PS1 = 'Push-PendingChanges.ps1'
FD = os.path.join(T, 'fsr_details.html')
ROUNDS_FILE = 'alv_rounds.py'

# The two fixtures, checked by hash so a wrong copy cannot slip in. The
# Bootstrap one is the file base.html's own SRI hash names:
# sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy
FIXTURES = {
    'test_fixture_jquery360.js':
        'ff1523fb7389539c84c65aba19260648793bb4f5e29329d2ee8804bc37a3fe6e',
    'test_fixture_bootstrap413.js': None,   # filled below from its SRI
}
BS_SRI = 'ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy'

report, problems = [], []
planned = {}
CRLF = {}


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def plan(path, old, new, what):
    cur = planned[path][1] if path in planned else read(path)
    if new and new in cur and old not in cur:
        return
    if cur.count(old) != 1:
        problems.append('%s: %s - anchor found %d time(s), expected 1'
                        % (path, what, cur.count(old)))
        return
    orig = planned[path][0] if path in planned else cur
    planned[path] = (orig, cur.replace(old, new, 1))
    report.append('%-44s %s' % (os.path.basename(path), what))


# ---- 1. the template ------------------------------------------------------
OLD_ISSUE = r"""            <div id="editIssueModal" class="ei-modal">
                <div class="ei-modal-dialog">
                    <div class="ei-modal-content">
                        <div class="ei-modal-header alv-modal-head">
                            <h2>Edit Issue</h2>
                            <button type="button" class="ei-modal-close" onclick="closeEditIssueModal()">&times;</button>
                        </div>
                        <form method="post" action="{% url 'fsr_edit_commit' isresults.issues_id %}">
                            {% csrf_token %}
                            <input type="hidden" name="from" value="{{ request.GET.from|default:'fsr' }}">
                            <div class="ei-modal-body">
                                <label class="ei-label" for="ei_heading">Issue Heading <span class="alv-req">*</span></label>
                                <input type="text" id="ei_heading" name="issues_heading" class="ei-input" maxlength="255" required value="{{ isresults.issues_heading|default:'' }}">

                                <label class="ei-label" for="ei_description">Description</label>
                                <textarea id="ei_description" name="issues_description" class="ei-input" rows="3" maxlength="255">{{ isresults.issues_description|default:'' }}</textarea>

                                <label class="ei-label" for="ei_prop">Property <span class="alv-req">*</span></label>
                                <select id="ei_prop" name="prop" class="ei-input" required>
                                    {% for p in props %}
                                    <option value="{{ p.prop_id }}" {% if p.prop_id == isresults.prop_id %}selected{% endif %}>{{ p.prop_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="ei-modal-footer">
                                <button type="button" class="btn action-secondary" onclick="closeEditIssueModal()">Cancel</button>
                                <button type="submit" class="btn action-primary">Save Changes</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
"""
NEW_ISSUE = r"""            <div class="modal fade" id="editIssueModal" tabindex="-1" role="dialog" aria-labelledby="editIssueModalTitle" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header alv-modal-head">
                            <h5 class="modal-title" id="editIssueModalTitle">Edit Issue</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <form method="post" action="{% url 'fsr_edit_commit' isresults.issues_id %}">
                            {% csrf_token %}
                            <input type="hidden" name="from" value="{{ request.GET.from|default:'fsr' }}">
                            <div class="modal-body">
                                <div class="form-group">
                                    <label for="ei_heading"><strong>Issue Heading</strong> <span class="alv-req">*</span></label>
                                    <input type="text" id="ei_heading" name="issues_heading" class="form-control" maxlength="255" required value="{{ isresults.issues_heading|default:'' }}">
                                </div>
                                <div class="form-group">
                                    <label for="ei_description"><strong>Description</strong></label>
                                    <textarea id="ei_description" name="issues_description" class="form-control" rows="3" maxlength="255">{{ isresults.issues_description|default:'' }}</textarea>
                                </div>
                                <div class="form-group">
                                    <label for="ei_prop"><strong>Property</strong> <span class="alv-req">*</span></label>
                                    <select id="ei_prop" name="prop" class="form-control" required>
                                        {% for p in props %}
                                        <option value="{{ p.prop_id }}" {% if p.prop_id == isresults.prop_id %}selected{% endif %}>{{ p.prop_name }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                                <button type="submit" class="btn action-primary">Save Changes</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
"""
OLD_COMMENT = r"""            <div id="editCommentModal" class="ei-modal">
                <div class="ei-modal-dialog">
                    <div class="ei-modal-content">
                        <div class="ei-modal-header alv-modal-head">
                            <h2>Edit Comment</h2>
                            <button type="button" class="ei-modal-close" onclick="closeEditCommentModal()">&times;</button>
                        </div>
                        <form method="post" action="{% url 'fsr_comment_edit_commit' %}">
                            {% csrf_token %}
                            <input type="hidden" name="from" value="{{ request.GET.from|default:'fsr' }}">
                            <input type="hidden" name="comment_id" id="ec_comment_id" value="">
                            <div class="ei-modal-body">
                                <label class="ei-label" for="ec_text">Comment <span class="alv-req">*</span></label>
                                <textarea id="ec_text" name="issues_details_comment" class="ei-input" rows="4" maxlength="255" required></textarea>
                                <p class="ec-note">You can edit only your own comments, and only until they&rsquo;ve been sent via &ldquo;Notify Now&rdquo;.</p>
                            </div>
                            <div class="ei-modal-footer">
                                <button type="button" class="btn action-secondary" onclick="closeEditCommentModal()">Cancel</button>
                                <button type="submit" class="btn action-primary">Save Comment</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
"""
NEW_COMMENT = r"""            <div class="modal fade" id="editCommentModal" tabindex="-1" role="dialog" aria-labelledby="editCommentModalTitle" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header alv-modal-head">
                            <h5 class="modal-title" id="editCommentModalTitle">Edit Comment</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <form method="post" action="{% url 'fsr_comment_edit_commit' %}">
                            {% csrf_token %}
                            <input type="hidden" name="from" value="{{ request.GET.from|default:'fsr' }}">
                            <input type="hidden" name="comment_id" id="ec_comment_id" value="">
                            <div class="modal-body">
                                <div class="form-group">
                                    <label for="ec_text"><strong>Comment</strong> <span class="alv-req">*</span></label>
                                    <textarea id="ec_text" name="issues_details_comment" class="form-control" rows="4" maxlength="255" required></textarea>
                                    <p class="form-text">You can edit only your own comments, and only until they&rsquo;ve been sent via &ldquo;Notify Now&rdquo;.</p>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                                <button type="submit" class="btn action-primary">Save Comment</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
"""
OLD_CSS = r"""/* ===== Issue edit: button, modal, history (added) ===== */
.ei-modal { display: none; position: fixed; z-index: 1050; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background: rgba(0,0,0,0.5); }
.ei-modal.show { display: block; }
.ei-modal-dialog { max-width: 560px; margin: 40px auto; padding: 0 12px; }
.ei-modal-content { background: var(--alv-paper); border-radius: 10px; overflow: hidden; box-shadow: 0 5px 20px rgba(0,0,0,0.3); }
.ei-modal-header { background: linear-gradient(135deg, var(--alv-accent) 0%, var(--alv-accent-ink) 100%); color: var(--alv-on-accent); padding: 16px 22px; display: flex; justify-content: space-between; align-items: center; }
.ei-modal-header h2 { margin: 0; font-size: 20px; }
.ei-modal-close { background: none; border: none; color: var(--alv-on-accent); font-size: 26px; line-height: 1; cursor: pointer; }
.ei-modal-body { padding: 22px; }
.ei-label { font-weight: 600; color: var(--alv-ink); margin: 14px 0 6px; display: block; }
.ei-label:first-child { margin-top: 0; }
.ei-input { width: 100%; border: 2px solid var(--alv-line); border-radius: 6px; padding: 9px 12px; font-size: 14px; font-family: inherit; line-height: 1.4; }
.ei-input:focus { border-color: var(--alv-accent); outline: none; box-shadow: 0 0 0 3px rgba(14, 124, 139,0.1); }
.ei-modal-footer { padding: 14px 22px; background: var(--alv-surface); display: flex; justify-content: flex-end; gap: 10px; }

"""
NEW_CSS = r"""/* ===== Edit history (added) ===== */
/* The Edit Issue and Edit Comment pop-ups are Bootstrap modals since
   21 Sep: base owns their header, and their fields are base's .form-group,
   label, .form-control and .form-text. Their own page rules went with
   them - see apply_ei_modal.py and test_ei_modal.py. */

"""
OLD_PHONE = r"""@media screen and (max-width: 768px) {
    .ei-modal-dialog { margin: 0; max-width: 100%; padding: 0; }
    .ei-modal-content { min-height: 100vh; border-radius: 0; }
}
"""
OLD_NOTE = r""".ec-note { color: var(--alv-ink-soft); font-size: 12px; margin: 10px 0 0; }
"""
OLD_JS = r"""<script>
// Edit Issue modal controls (self-contained; not Bootstrap)
function openEditIssueModal() {
    var m = document.getElementById('editIssueModal');
    if (m) m.classList.add('show');
}
function closeEditIssueModal() {
    var m = document.getElementById('editIssueModal');
    if (m) m.classList.remove('show');
}
document.addEventListener('click', function(e) {
    var m = document.getElementById('editIssueModal');
    if (m && e.target === m) closeEditIssueModal();
});
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeEditIssueModal();
});
</script>

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
"""
NEW_JS = r"""<script>
// Edit Issue and Edit Comment - Bootstrap modals since 21 Sep. Bootstrap
// closes them on Escape, on the backdrop and on anything carrying
// data-dismiss, so only opening is left here. The names stay because the
// page's buttons call them.
function openEditIssueModal() {
    $('#editIssueModal').modal('show');
}
function closeEditIssueModal() {
    $('#editIssueModal').modal('hide');
}
function openEditCommentModal(btn) {
    var id = btn.getAttribute('data-comment-id');
    var text = btn.getAttribute('data-comment-text') || '';
    var idEl = document.getElementById('ec_comment_id');
    var textEl = document.getElementById('ec_text');
    if (idEl) idEl.value = id;
    if (textEl) textEl.value = text;
    $('#editCommentModal').modal('show');
}
function closeEditCommentModal() {
    $('#editCommentModal').modal('hide');
}
</script>
"""

if not os.path.isfile(FD):
    problems.append('%s not found' % FD)
else:
    d = read(FD)
    if 'class="ei-' not in d and 'id="editIssueModal"' in d \
            and '.ei-' not in d:
        report.append('%-44s already done' % 'fsr_details.html')
    else:
        plan(FD, OLD_ISSUE, NEW_ISSUE, 'Edit Issue -> Bootstrap modal, '
             'base fields')
        plan(FD, OLD_COMMENT, NEW_COMMENT, 'Edit Comment -> Bootstrap '
             'modal, base fields')
        plan(FD, OLD_CSS, NEW_CSS, '14 .ei-* rules removed')
        plan(FD, OLD_PHONE, '', 'the phone block that held only .ei-* '
             'rules removed')
        plan(FD, OLD_NOTE, '', '.ec-note removed (now .form-text)')
        plan(FD, OLD_JS, NEW_JS, 'script: Bootstrap opens and closes')

# ---- 2. test_fsr_palette.py: LATER ----------------------------------------
PAL = 'test_fsr_palette.py'
PAL_EDITS = [
    ("""check('the gradient header takes on-accent ink, not paper',
      re.search(r'\\.ei-modal-header\\s*\\{[^}]*color:\\s*var\\(--alv-on-accent\\)',
                css_of(DNC)) is not None)
check('  and the dialog itself takes paper',
      re.search(r'\\.ei-modal-content\\s*\\{[^}]*background:\\s*var\\(--alv-paper\\)',
                css_of(DNC)) is not None)""",
     """# LATER - test_ei_modal.py, 21 Sep: the .ei-* pop-ups became Bootstrap
# modals and their rules went. This round's decision is judged on the file
# as it LEFT it - the eimodal backup when there is one.
_FDL = (nocomment(read(FD + '.bak_eimodal'))
        if os.path.exists(FD + '.bak_eimodal') else DNC)
check('the gradient header takes on-accent ink, not paper',
      re.search(r'\\.ei-modal-header\\s*\\{[^}]*color:\\s*var\\(--alv-on-accent\\)',
                css_of(_FDL)) is not None)
check('  and the dialog itself takes paper',
      re.search(r'\\.ei-modal-content\\s*\\{[^}]*background:\\s*var\\(--alv-paper\\)',
                css_of(_FDL)) is not None)"""),
    ("""    check('  .. but %-18s survives - only the unused one went' % sel,
          sel in css_of(DNC))""",
     """    check('  .. but %-18s survives - only the unused one went' % sel,
          sel in css_of(_FDL))"""),
]
if os.path.isfile(PAL):
    for old, new in PAL_EDITS:
        plan(PAL, old, new, 'LATER: reads .ei-* from the file as its round '
             'left it')
else:
    report.append('%-44s not on disk - nothing to adjust' % PAL)

# ---- 2b. test_print_queries.py: LATER --------------------------------------
# Its probe section compared the file NOW with its backup, block for block.
# This round deletes a phone block from fsr_details that held only .ei-*
# rules, so the counts differ though its own round did nothing wrong. The
# whole-suite sweep caught it. It now asks alv_rounds for the file as its
# round left it, like the rest of that suite already does.
PQ = 'test_print_queries.py'
if os.path.isfile(PQ):
    plan(PQ, """        for rel, p in TOUCHED:
            now, was = read(p), read(p + SUFFIX)
            s_now, pr_now = block_probes(now, 'n')""",
         """        from alv_rounds import as_left_by
        for rel, p in TOUCHED:
            # LATER - test_ei_modal.py, 21 Sep: the file as THIS round left
            # it; a later round may delete a block that was never ours.
            now, was = as_left_by(p, SUFFIX, read), read(p + SUFFIX)
            s_now, pr_now = block_probes(now, 'n')""",
         'LATER: probes the file as its round left it')
else:
    report.append('%-44s not on disk - nothing to adjust' % PQ)

# ---- 3. alv_rounds.py -----------------------------------------------------
if not os.path.isfile(ROUNDS_FILE):
    problems.append('%s missing - apply_modal_heads.py first' % ROUNDS_FILE)
else:
    plan(ROUNDS_FILE, "    '.bak_modalhead',\n]",
         "    '.bak_modalhead',\n    '.bak_eimodal',\n]",
         'learns .bak_eimodal')

# ---- 4. fixtures ----------------------------------------------------------
NEW_FILES = {}
for name in FIXTURES:
    src = os.path.join(HERE, name)
    if os.path.isfile(name):
        src = name
    if not os.path.isfile(src):
        problems.append('%s must sit beside this patcher' % name)
        continue
    data = open(src, 'rb').read()
    if name == 'test_fixture_bootstrap413.js':
        import base64
        ok = base64.b64encode(hashlib.sha384(data).digest()).decode() == BS_SRI
    else:
        ok = hashlib.sha256(data).hexdigest() == FIXTURES[name]
    if not ok:
        problems.append('%s: hash does not match the release' % name)
    elif not os.path.isfile(name):
        NEW_FILES[name] = data
        report.append('%-44s new fixture, hash checked' % name)

# ---- 5. the gate ----------------------------------------------------------
GATE_NOTE = """    # The Issue page's two edit pop-ups are Bootstrap modals with base's
    # header and base's fields. Its render runs the real jQuery and
    # Bootstrap from two fixture files, opens both, fills the comment, and
    # closes them on Escape, the backdrop and Cancel.
    # Newest, so most likely to be what breaks.
    'test_ei_modal.py'"""
if os.path.isfile(PS1):
    psrc = planned[PS1][1] if PS1 in planned else read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-44s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$",
                          psrc[i:i + m.start()]) if m else None)
        if not last:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-44s + %s, after %s' % (PS1, SUITE,
                                                    last.group(1)))

# ==========================================================================
# SELF-CHECK
# ==========================================================================
for path, (src, text) in planned.items():
    if path.endswith('.py'):
        try:
            ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: does not parse - line %s' % (path, e.lineno))
if FD in planned:
    src, text = planned[FD]
    if re.search(r'\bei-(modal|label|input)|ec-note', text):
        problems.append('fsr_details.html: an .ei-* name survives')
    for tag in ('{% if', '{% endif %}', '{% for', '{% endfor %}',
                '{% csrf_token %}', '{% url'):
        if src.count(tag) != text.count(tag):
            problems.append('fsr_details.html: %s count changed' % tag)
    for attr in ('id="ei_heading"', 'name="issues_heading"',
                 'id="ei_description"', 'name="issues_description"',
                 'id="ei_prop"', 'name="prop"', 'id="ec_text"',
                 'name="issues_details_comment"', 'id="ec_comment_id"',
                 'name="comment_id"', 'onclick="openEditIssueModal()"',
                 'onclick="openEditCommentModal(this)"'):
        if src.count(attr) != text.count(attr):
            problems.append('fsr_details.html: %s count changed' % attr)
    rest_a = src
    for o in (OLD_ISSUE, OLD_COMMENT, OLD_CSS, OLD_PHONE, OLD_NOTE, OLD_JS):
        rest_a = rest_a.replace(o, '')
    rest_b = text
    for n in (NEW_ISSUE, NEW_COMMENT, NEW_CSS, NEW_JS):
        rest_b = rest_b.replace(n, '')
    if rest_a != rest_b:
        problems.append('fsr_details.html: more changed than the six blocks')

print('\n' + '=' * 74)
print('THE ISSUE PAGE\'S EDIT POP-UPS - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned and not NEW_FILES:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
for name, data in NEW_FILES.items():
    with open(name, 'wb') as f:
        f.write(data)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
if NEW_FILES:
    print('  new: %s' % ', '.join(sorted(NEW_FILES)))
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
