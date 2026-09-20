# -*- coding: utf-8 -*-
"""apply_admin_stage_e.py - the last two hand-rolled tables.

    python apply_admin_stage_e.py --check
    python apply_admin_stage_e.py
    python test_table_admin.py
    python Push-PendingChanges.ps1

user_administration and workspace_management are the last two pages in the
system still rolling their own table. Every other list reads

    <div class="table-container">
      <table class="table alv-table suppliers-table">

and these two read

    <div class="user-table">          <div class="workspace-table">
      <table>                           <table>        <- no class at all

They also hand-roll the phone card conversion - `.user-table table,
.user-table thead, .user-table tbody, .user-table tr, .user-table td
{ display: block }` and a `::before` per column carrying the heading - which
is exactly what .alv-table does at 768px, and does with `data-label` so the
heading travels with the cell rather than with its position.

THIS IS THE TWELFTH TIME THIS MIGRATION HAS BEEN DONE. The mechanics are
settled; what needed deciding was three things, and they were decided on
20 Sep:

  1. A ROLE IS A CATEGORY, NOT A VERDICT, so the three role badges become
     .alv-tag-* - the call stage C made when workspace-badge did. Superuser
     plum, Staff sky, User slate. NO ORDER IS IMPLIED and that is the point:
     base states the tag tones are categories and not a scale, and
     asset_detail already maps five maintenance types onto the five tones
     with no ranking. Slate is the quietest and already the neutral-ish tone
     on property_assets and property_report, so the commonest role reads as
     the plain case.

     Active/Disabled become .alv-pill-good / .alv-pill-neutral - GREY, NOT
     RED, matching Properties and Tenants where Inactive was deliberately
     taken off the danger scale. The 8px dot goes: no migrated pill carries
     one.

  2. TWO VERBS BASE HAD NO NAME FOR, and the house rule from the Invoices
     round is a NAME ON AN EXISTING COLOUR, NEVER A NEW COLOUR. So
     .icon-permissions on --alv-view as .icon-manage is, and .icon-lock /
     .icon-unlock on the amber and green .icon-unapprove / .icon-approve
     already use.

     THEY ARE NOT CALLED .icon-disable. base already has .icon-disabled, a
     STATE on a control the user may not use. Two classes one character
     apart in one stylesheet is how \\bform-section\\b came to match inside
     form-section-title, and that cost a round. Reusing .icon-approve on an
     Enable button was the other option and was rejected: a name that lies
     is what these rounds keep having to undo.

  3. THE EMPTY STATES, in the unfiltered house voice - name the thing, then
     say what adding one does. Neither page has filters, so the "try
     clearing the filters" form does not apply.

TWO THINGS THE 18 SEP SURVEY GOT WRONG, corrected by reading the pages:

  * workspace_management DOES have an empty state. It is hand-rolled,
    outside the table, wrapped in {% if workspaces %}...{% else %}, and
    carries an inline style="font-weight: 600". So that one is a MIGRATION
    into {% empty %}-style markup as .alv-empty, not a composition.

  * A WORKSPACE IS NOT A GROUPING OF PROPERTIES. Its own delete modal says
    what it holds: "All Passports, Celebrations, and Recipes belonging to
    this workspace will be permanently removed." It is the Personal
    module's container. An empty state calling it a property grouping would
    have been wrong and would have read as authoritative.

AND ONE THIS ROUND FOUND: user_administration's Delete button already wears
btn-disable with a trash glyph. A name that lies, in the file, today. It
becomes .icon-delete delete-btn, which is what it is.

WHAT IS NOT CHANGED, logged: workspace_management spells its Help button's
label .action-back-label. base only hides that span inside an .action-back,
so it is inert - a wrong name, not a wrong render. Noted at stage C, still
true, still not urgent, and not this round's business.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_stagee'
SUITE = 'test_table_admin.py'
PS1 = 'Push-PendingChanges.ps1'

report, problems, removed = [], [], []
CRLF = {}


def read(p):
    """Text as LF, and remember what the file actually used.

    A patcher that changes a table must not also rewrite every line of the
    file it is in. Python's text mode turns CRLF into LF on the way in and
    writing back with newline='' then emits LF, so an earlier round in this
    programme silently converted four templates and two tools and put every
    line of them in the commit."""
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def markup_only(text):
    out = list(text)
    for m in re.finditer(r'<(script|style)[^>]*>(.*?)</\1>', text, re.S):
        for i in range(m.start(2), m.end(2)):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def close_of(text, after_open):
    """End of the <div> whose opening tag ends at `after_open`."""
    depth = 1
    for m in re.finditer(r'<div\b[^>]*>|</div>', text[after_open:]):
        depth += 1 if m.group(0) != '</div>' else -1
        if depth == 0:
            return after_open + m.end()
    return None


def expressions(text):
    """Every Django expression in the block, as a sorted multiset.

    THE ONE INVARIANT A REBUILT TABLE HAS. The markup around them is
    replaced wholesale, so a diff says nothing; what must not change is the
    DATA the block reads and the branches it reads it in. Whitespace inside
    a tag is normalised, because re-indenting a tag is not losing it."""
    out = []
    for m in re.finditer(r'\{\{.*?\}\}|\{%.*?%\}', text, re.S):
        out.append(re.sub(r'\s+', ' ', m.group(0)).strip())
    return sorted(out)


# ==========================================================================
# 1. base.html - three names on existing colours
# ==========================================================================
BASE_ANCHOR = '.icon-color-manage { color: var(--alv-view); }\n'
BASE_ADD = """
/* Permissions, lock and unlock: three more NAMES ON EXISTING COLOURS, for
   Administration's user list. Same rule as Duplicate, Upload and Manage
   above - no new hex enters the palette.

   Permissions opens a screen that shows what a user MAY do, which is a
   view, so it wears --alv-view exactly as .icon-manage does.

   Lock and unlock are Disable and Enable. By shape they are the pair that
   .icon-unapprove and .icon-approve already are - amber and green, a state
   you can toggle back - and they take their own names rather than
   borrowing those, because an Enable button carrying a class called
   `approve` says something the button does not do.

   AND THEY ARE NOT CALLED .icon-disable. base already has .icon-disabled,
   which is a STATE on a control the user may not use, not an action. Two
   class names one character apart in one stylesheet is how
   `\\bform-section\\b` came to match inside `form-section-title` and cost
   this project a round; the edge of a class name is not a word boundary,
   and the cheapest moment to avoid that is before the name exists. */
.icon-permissions       { color: var(--alv-view); border-color: var(--alv-accent-line); }
.icon-permissions:hover { background-color: var(--alv-view); border-color: var(--alv-view); color: var(--alv-on-accent); }
.icon-color-permissions { color: var(--alv-view); }

.icon-lock       { color: var(--alv-warn); border-color: #ecd9a8; }
.icon-lock:hover { background-color: var(--alv-warn); border-color: var(--alv-warn); color: #fff; }
.icon-color-lock { color: var(--alv-warn); }

.icon-unlock       { color: var(--alv-good); border-color: #bfe0cd; }
.icon-unlock:hover { background-color: var(--alv-good); border-color: var(--alv-good); color: #fff; }
.icon-color-unlock { color: var(--alv-good); }
"""

planned = {}

BASE = os.path.join(ROOT, 'base.html')
if not os.path.isfile(BASE):
    problems.append('base.html: not found')
else:
    src = read(BASE)
    if '.icon-permissions' in src:
        report.append('%-28s already has the three names' % 'base.html')
    elif src.count(BASE_ANCHOR) != 1:
        problems.append('base.html: the .icon-color-manage line appears %d '
                        'time(s), expected 1' % src.count(BASE_ANCHOR))
    else:
        at = src.index(BASE_ANCHOR) + len(BASE_ANCHOR)
        planned[BASE] = (src, src[:at] + BASE_ADD + src[at:])
        report.append('%-28s + .icon-permissions, .icon-lock, .icon-unlock '
                      '(and their mobile colours)' % 'base.html')


# ==========================================================================
# 2. THE TWO TABLES, rebuilt onto the standard
# ==========================================================================
USERS_TABLE = '''    <!-- Users (desktop) / Card list (mobile) -->
    <div class="table-container">
        <table class="table alv-table users-table">
            <thead>
                <tr>
                    <th style="text-align: left; width: 30%">User</th>
                    <th style="width: 12%">Role</th>
                    <th style="width: 12%">Status</th>
                    <th style="width: 16%">Last Login</th>
                    <th style="width: 14%">Date Joined</th>
                    <th class="desktop-action-cell cell-actions" style="width: 16%">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <td data-label="User" style="text-align: left">
                        <div class="user-info">
                            <div class="user-avatar">
                                {% if user.profile.profile_photo %}
                                    <img src="{{ user.profile.profile_photo.url }}" alt="{{ user.username }}">
                                {% elif user.first_name and user.last_name %}
                                    {{ user.first_name|first|upper }}{{ user.last_name|first|upper }}
                                {% else %}
                                    {{ user.username|first|upper }}
                                {% endif %}
                            </div>
                            <div>
                                <div class="user-name">{{ user.get_full_name|default:user.username }}</div>
                                <div class="user-email">{{ user.email|default:"No email" }}</div>
                                <div class="user-workspace">
                                    <i class="fas fa-layer-group"></i>
                                    {% if user.profile.workspace %}
                                        {{ user.profile.workspace.name }}
                                    {% else %}
                                        <span class="user-workspace-none">No workspace</span>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </td>
                    <td data-label="Role">
                        {% if user.is_superuser %}
                            <span class="alv-tag alv-tag-plum"><i class="fas fa-crown"></i> Superuser</span>
                        {% elif user.is_staff %}
                            <span class="alv-tag alv-tag-sky"><i class="fas fa-user-tie"></i> Staff</span>
                        {% else %}
                            <span class="alv-tag alv-tag-slate"><i class="fas fa-user"></i> User</span>
                        {% endif %}
                    </td>
                    <td data-label="Status">
                        <span class="alv-pill {% if user.is_active %}alv-pill-good{% else %}alv-pill-neutral{% endif %}">
                            {% if user.is_active %}Active{% else %}Disabled{% endif %}
                        </span>
                    </td>
                    <td data-label="Last Login">
                        {% if user.last_login %}
                            {{ user.last_login|date:"d M Y H:i" }}
                        {% else %}
                            <span class="text-muted">Never</span>
                        {% endif %}
                    </td>
                    <td data-label="Date Joined">{{ user.date_joined|date:"d M Y" }}</td>
                    <!-- Desktop actions: one cell -->
                    <td class="desktop-action-cell cell-actions">
                        <span class="row-actions">
                            <a href="{% url 'user_edit' user.id %}" class="icon-action-btn icon-edit" title="Edit User">
                                <i class="fas fa-pencil-alt"></i>
                            </a>
                            <a href="{% url 'user_permissions' user.id %}" class="icon-action-btn icon-permissions" title="Manage Permissions">
                                <i class="fas fa-key"></i>
                            </a>
                            {% if user.is_active %}
                                <button type="button" class="icon-action-btn icon-lock" title="Disable User"
                                        onclick="confirmToggle({{ user.id }}, '{{ user.username }}', false)">
                                    <i class="fas fa-ban"></i>
                                </button>
                            {% else %}
                                <button type="button" class="icon-action-btn icon-unlock" title="Enable User"
                                        onclick="confirmToggle({{ user.id }}, '{{ user.username }}', true)">
                                    <i class="fas fa-check"></i>
                                </button>
                                <button type="button" class="icon-action-btn icon-delete delete-btn" title="Delete User"
                                        onclick="confirmDelete({{ user.id }}, '{{ user.username }}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            {% endif %}
                        </span>
                    </td>
                    <!-- Mobile-only action bar (hidden on desktop) -->
                    <td class="mobile-action-bar">
                        <a href="{% url 'user_edit' user.id %}" class="mobile-action-btn">
                            <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
                            <span class="mobile-action-label">Edit</span>
                        </a>
                        <a href="{% url 'user_permissions' user.id %}" class="mobile-action-btn">
                            <i class="fas fa-key mobile-action-icon icon-color-permissions"></i>
                            <span class="mobile-action-label">Permissions</span>
                        </a>
                        {% if user.is_active %}
                            <button type="button" class="mobile-action-btn"
                                    onclick="confirmToggle({{ user.id }}, '{{ user.username }}', false)">
                                <i class="fas fa-ban mobile-action-icon icon-color-lock"></i>
                                <span class="mobile-action-label">Disable</span>
                            </button>
                        {% else %}
                            <button type="button" class="mobile-action-btn"
                                    onclick="confirmToggle({{ user.id }}, '{{ user.username }}', true)">
                                <i class="fas fa-check mobile-action-icon icon-color-unlock"></i>
                                <span class="mobile-action-label">Enable</span>
                            </button>
                            <button type="button" class="mobile-action-btn"
                                    onclick="confirmDelete({{ user.id }}, '{{ user.username }}')">
                                <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                                <span class="mobile-action-label">Delete</span>
                            </button>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        {% if not users %}
            {# An empty tbody looks exactly like a failed load. #}
            <div class="alv-empty">
                <i class="fas fa-users"></i>
                <div class="alv-empty-title">No users yet</div>
                <div class="alv-empty-hint">
                    Add a user to give someone access; their role and permissions are set from this list.
                </div>
            </div>
        {% endif %}
    </div>
'''

WORKSPACES_TABLE = '''    <!-- Workspaces (desktop) / Card list (mobile) -->
    <div class="table-container">
        <table class="table alv-table workspaces-table">
            <thead>
                <tr>
                    <th style="text-align: left; width: 30%">Name</th>
                    <th style="width: 24%">Owner</th>
                    <th style="width: 14%">Members</th>
                    <th style="width: 18%">Updated</th>
                    <th class="desktop-action-cell cell-actions" style="width: 14%">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for ws in workspaces %}
                <tr>
                    <td data-label="Name" style="text-align: left">
                        <div class="ws-name">
                            <i class="fas fa-layer-group"></i>
                            {{ ws.name }}
                        </div>
                    </td>
                    <td data-label="Owner">
                        <div class="ws-owner-name">{{ ws.owner.get_full_name|default:ws.owner.username }}</div>
                        {% if ws.owner.get_full_name %}
                        <div class="ws-owner-username">{{ ws.owner.username }}</div>
                        {% endif %}
                    </td>
                    <td data-label="Members">
                        <span class="ws-members" title="{% for m in ws.member_list %}{{ m.user.username }}{% if not forloop.last %}, {% endif %}{% endfor %}">
                            <i class="fas fa-users"></i> {{ ws.member_count }}
                        </span>
                    </td>
                    <td data-label="Updated">{{ ws.updated_at|date:"d M Y H:i" }}</td>
                    <!-- Desktop actions: one cell -->
                    <td class="desktop-action-cell cell-actions">
                        <span class="row-actions">
                            <a href="{% url 'workspace_edit' ws.id %}" class="icon-action-btn icon-edit" title="Edit Workspace">
                                <i class="fas fa-pencil-alt"></i>
                            </a>
                            {% if ws.member_count == 0 %}
                                <button type="button" class="icon-action-btn icon-delete delete-btn" title="Delete Workspace"
                                        onclick="confirmDelete({{ ws.id }}, '{{ ws.name|escapejs }}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            {% else %}
                                <span class="icon-action-btn icon-disabled" title="Cannot delete: workspace has members">
                                    <i class="fas fa-trash"></i>
                                </span>
                            {% endif %}
                        </span>
                    </td>
                    <!-- Mobile-only action bar (hidden on desktop) -->
                    <td class="mobile-action-bar">
                        <a href="{% url 'workspace_edit' ws.id %}" class="mobile-action-btn">
                            <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
                            <span class="mobile-action-label">Edit</span>
                        </a>
                        {% if ws.member_count == 0 %}
                            <button type="button" class="mobile-action-btn delete-btn-mobile"
                                    onclick="confirmDelete({{ ws.id }}, '{{ ws.name|escapejs }}')">
                                <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                                <span class="mobile-action-label">Delete</span>
                            </button>
                        {% else %}
                            <span class="mobile-action-btn mobile-action-disabled" title="Cannot delete: workspace has members">
                                <i class="fas fa-trash mobile-action-icon"></i>
                                <span class="mobile-action-label">Delete</span>
                            </span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        {% if not workspaces %}
            {# An empty tbody looks exactly like a failed load. #}
            <div class="alv-empty">
                <i class="fas fa-layer-group"></i>
                <div class="alv-empty-title">No workspaces yet</div>
                <div class="alv-empty-hint">
                    Add a workspace to hold a set of Passports, Celebrations and Recipes.
                </div>
            </div>
        {% endif %}
    </div>
'''

# (rel, the div class that wraps the old table, the new block, the
#  expressions the rebuild is ALLOWED to drop, and why)
TABLES = [
    ('user_administration.html', 'user-table', USERS_TABLE, {}),
    # workspace_management wraps its table in {% if workspaces %} ...
    # {% else %} <div class="empty-state"> ... {% endif %}. The rebuild puts
    # the empty state INSIDE .table-container as .alv-empty, the way every
    # migrated list does, so that wrapper goes. MEASURED, not assumed: the
    # only expression actually lost is `{% if workspaces %}` - it is
    # replaced by `{% if not workspaces %}`, and the else/endif counts go
    # UP, not down, because the mobile action bar brings its own.
    ('workspace_management.html', 'workspace-table', WORKSPACES_TABLE,
     {'{% if workspaces %}': 1}),
]

# ==========================================================================
# 3. THE PAGE-LOCAL RULES THE STANDARD MAKES REDUNDANT
#
# A RULE, NOT A LIST: any rule whose selector names one of these classes
# goes, wherever it sits, including inside an @media block - and a media
# block left with nothing in it goes too. The class name is matched at its
# EDGES, because `.action-btn` must not take `.action-more-btn` with it.
# That is the same guard push 1 needed when \bform-section\b matched inside
# form-section-title.
# ==========================================================================
DROP_CLASSES = {
    'user_administration.html': [
        'user-table', 'badge-superuser', 'badge-staff', 'badge-user',
        'status-active', 'status-inactive', 'action-btn',
        'btn-edit', 'btn-permissions', 'btn-disable', 'btn-enable'],
    'workspace_management.html': [
        'workspace-table', 'action-btn', 'btn-edit', 'btn-delete',
        'empty-state'],
}
# Kept on purpose: .user-avatar .user-info .user-name .user-email
# .user-workspace .ws-name .ws-owner-name .ws-owner-username .ws-members -
# these style the CONTENT of a cell, which the migration does not touch -
# and .user-admin-container / .workspace-admin-container, which are layout.
CLASS_EDGE = r'(?<![\w-])\.%s(?![\w-])'


COMMENT = re.compile(r'/\*.*?\*/', re.S)
TRAILING_COMMENTS = re.compile(r'(?:\s*/\*.*?\*/)+\s*$', re.S)


def strip_rules(css, classes):
    """Remove every rule naming one of the classes, nesting-aware.

    A COMMENT IS NOT A SELECTOR, and the first draft of this function
    forgot it. The text between one `}` and the next `{` is the selector
    list AND anything written above it, so

        /* First cell - User info - stays as-is, no label */
        .user-table tbody td:nth-child(1) { ... }

    split on commas into TWO 'selectors', only the second of which named a
    class to drop. The half-comment was therefore 'kept' and emitted with
    the next rule's braces welded to it:

        }/* First cell - User info - stays as-is{

    That is the fifth time in this project a CSS comment has been mistaken
    for something it is not - a comment in front of @media hiding the
    block, a comment inside a rule body, and now a comment with a comma in
    it. So: comments are lifted out of the selector text before it is split
    at all, and a comment sitting directly above a rule that IS dropped
    goes with it, because a comment describing markup that no longer exists
    is debt, not documentation.

    Returns (css, [selectors removed])."""
    gone = []

    def walk(block):
        out, i, n = [], 0, len(block)
        while i < n:
            at = re.compile(r'@media([^{]*)\{').search(block, i)
            rule = re.compile(r'([^{}@]+)\{([^{}]*)\}').search(block, i)
            if at and (not rule or at.start() < rule.start()):
                depth, j = 1, at.end()
                while j < n and depth:
                    if block[j] == '{':
                        depth += 1
                    elif block[j] == '}':
                        depth -= 1
                    j += 1
                inner = walk(block[at.end():j - 1])
                out.append(block[i:at.start()])
                # A MEDIA BLOCK WITH NOTHING LEFT IN IT GOES. What remains
                # has to contain a brace - comments alone are not content.
                if '{' in inner:
                    out.append(block[at.start():at.end()] + inner + '}')
                i = j
                continue
            if not rule:
                out.append(block[i:])
                break

            out.append(block[i:rule.start()])
            sel_src = rule.group(1)
            # THE WHITESPACE BELONGS TO THE FILE, NOT TO THIS ROUND. The
            # separation between one rule and the next lives inside the
            # selector text, so rebuilding a rule that is being KEPT welds
            # it to the previous closing brace and reformats a file this
            # round had no business reformatting. A kept rule is emitted
            # exactly as it was found.
            indent = re.match(r'\s*', sel_src).group(0)
            sel_clean = COMMENT.sub('', sel_src)
            sels = [s.strip() for s in sel_clean.split(',') if s.strip()]
            hit = [s for s in sels
                   if any(re.search(CLASS_EDGE % re.escape(c), s)
                          for c in classes)]

            if sels and len(hit) == len(sels):
                # The rule goes, and so does the comment written above it -
                # a comment describing markup that no longer exists is
                # debt, not documentation. The blank line before it stays,
                # so what is left still reads as separate rules.
                out.append(indent)
                gone.append(' '.join(sel_clean.split())[:70])
            elif hit:
                # A COMPOUND RULE IS NOT AN ALL-OR-NOTHING RULE. Keep the
                # selectors that are not this round's, and say so.
                keep = [s for s in sels if s not in hit]
                out.append(indent + ''.join(COMMENT.findall(sel_src))
                           + ',\n'.join(keep) + ' {' + rule.group(2) + '}')
                gone.append('(partial) ' + ', '.join(hit)[:58])
            else:
                out.append(block[rule.start():rule.end()])
            i = rule.end()
        return ''.join(out)

    out = walk(css)
    # tidy: never leave more than one blank line where a rule was
    return re.sub(r'\n[ \t]*\n[ \t]*\n+', '\n\n', out), gone


for rel, wrapper, new_block, allowed_drop in TABLES:
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        problems.append('%s: not found' % rel)
        continue
    src = read(path)
    if 'table-container' in src:
        report.append('%-28s already migrated' % rel)
        continue
    text = src
    notes = []

    # --- the table ------------------------------------------------------
    opens = list(re.finditer(r'[ \t]*<div class="%s">\n' % wrapper, text))
    if len(opens) != 1:
        problems.append('%s: <div class="%s"> appears %d time(s), expected 1'
                        % (rel, wrapper, len(opens)))
        continue
    o = opens[0]
    end = close_of(text, o.end())
    if end is None:
        problems.append('%s: the .%s wrapper never closes' % (rel, wrapper))
        continue
    if text[end:end + 1] == '\n':
        end += 1
    start = o.start()
    # take a comment line immediately above it with the block
    ls = text.rfind('\n', 0, start - 1) + 1
    if re.match(r'[ \t]*<!--[^\n]*-->\n', text[ls:start]):
        start = ls
    # workspace_management wraps the whole thing in {% if workspaces %} ...
    # {% else %} <div class="empty-state"> ... {% endif %}
    old = text[start:end]
    tail = text[end:]
    pre = text[:start]
    m_if = re.search(r'[ \t]*\{%\s*if\s+workspaces\s*%\}\n$', pre)
    if m_if:
        m_else = re.match(r'[ \t]*\{%\s*else\s*%\}\n(.*?)'
                          r'[ \t]*\{%\s*endif\s*%\}\n', tail, re.S)
        if not m_else:
            problems.append('%s: the {%% if workspaces %%} opens and its '
                            '{%% else %%}/{%% endif %%} were not found' % rel)
            continue
        old = pre[m_if.start():] + old + tail[:m_else.end()]
        pre = pre[:m_if.start()]
        tail = tail[m_else.end():]

    lost = {}
    a, b = expressions(old), expressions(new_block)
    for e in set(a):
        d = a.count(e) - b.count(e)
        if d > 0:
            lost[e] = d
    unexpected = {k: v for k, v in lost.items() if allowed_drop.get(k) != v}
    if unexpected:
        problems.append('%s: the rebuild drops expression(s) the round did '
                        'not name - %s' % (rel, sorted(unexpected.items())))
        continue
    text = pre + new_block + tail
    notes.append('table rebuilt onto .alv-table (+ data-label, a mobile '
                 'action bar and an empty state)')

    # --- the rules ------------------------------------------------------
    def repl(m):
        css, gone = strip_rules(m.group(1), DROP_CLASSES[rel])
        removed.extend('%-28s %s' % (rel, g) for g in gone)
        return m.group(0)[:m.group(0).index('>') + 1] + css + '</style>'
    text = re.sub(r'<style[^>]*>(.*?)</style>', repl, text, flags=re.S)
    notes.append('%d page-local rule(s) removed'
                 % len([r for r in removed if r.startswith('%-28s' % rel)
                        or r.startswith(rel)]))

    planned[path] = (src, text)
    report.append('%-28s %s' % (rel, '; '.join(notes)))


# ==========================================================================
# 3b. A SUITE IS THE RECORD OF A DECISION, AND THIS ROUND CHANGES ONE
#
# test_print_leaks.py promises, in the present tense, that EVERY MEDIA QUERY
# a page had before that round is still there. It was right to promise it -
# deleting a guarded query is exactly the fault it exists to catch - and it
# already carries the mechanism for a later round that legitimately edits
# one: a LATER map naming that round's backup to compare against instead.
# Its own comment says two rounds have needed it in a week. This is the
# third.
#
# What stage E does to workspace_management is remove this, whole:
#
#     @media (hover: hover) {
#         .workspace-table tbody tr:hover { background: #f8f9fa; }
#         .action-btn:hover { transform: scale(1.1); }
#         .btn-delete.disabled:hover { transform: none; }
#     }
#
# Three rules, every one of them naming a class this round removes. The
# block empties, and an empty media query is not worth keeping. NOTHING IS
# LOST: base already supplies `.alv-table tbody tr:hover` - in the house
# accent rather than this page's own #f8f9fa - and `.icon-action-btn:hover`
# with a fill per icon name. The page-local hovers were a fifth
# implementation, which is what this migration is for.
#
# So the entry is added here, by the round that causes it, rather than left
# for whoever next runs the gate to puzzle out.
# ==========================================================================
LEAK_SUITE = 'test_print_leaks.py'
LEAK_ANCHOR = """LATER = {'finance/financial_indicators.html': '.bak_fiseg',
         'fsr.html': '.bak_iadrill'}"""
LEAK_NEW = """LATER = {'finance/financial_indicators.html': '.bak_fiseg',
         'fsr.html': '.bak_iadrill',
         # Administration stage E, 20 Sep. Its @media (hover: hover) held
         # three rules and every one of them named a class that round
         # removed, so the block emptied and went with them. base already
         # supplies .alv-table tbody tr:hover and .icon-action-btn:hover,
         # so no hover was lost - only a fifth copy of one. The query claim
         # is measured up to the point stage E began; what the file looks
         # like NOW is test_table_admin.py's business, and its section 3
         # asserts the block went because it emptied.
         'workspace_management.html': '.bak_stagee'}"""

if not os.path.isfile(LEAK_SUITE):
    report.append('%-28s not on disk - its LATER map is not updated'
                  % LEAK_SUITE)
else:
    lsrc = read(LEAK_SUITE)
    if "'workspace_management.html': '.bak_stagee'" in lsrc:
        report.append('%-28s already records this round' % LEAK_SUITE)
    elif lsrc.count(LEAK_ANCHOR) != 1:
        problems.append('%s: the LATER map appears %d time(s), expected 1'
                        % (LEAK_SUITE, lsrc.count(LEAK_ANCHOR)))
    else:
        planned[LEAK_SUITE] = (lsrc, lsrc.replace(LEAK_ANCHOR, LEAK_NEW, 1))
        report.append('%-28s + workspace_management in its LATER map, with '
                      'the reason' % LEAK_SUITE)


# ==========================================================================
# 4. THE GATE
# ==========================================================================
GATE_NOTE = """    # The last two hand-rolled tables joined the standard. Its
    # section 2 asserts the DATA the rebuilt blocks read is the data the
    # old ones read - the markup around it was replaced wholesale, so a
    # diff says nothing and the expressions are the only invariant there
    # is. Newest, so most likely to be what breaks.
    'test_table_admin.py'"""

ps1_new = None
if not os.path.isfile(PS1):
    report.append('%-28s not on disk - the suite is not wired' % PS1)
elif SUITE in read(PS1):
    report.append('%-28s already runs %s' % (PS1, SUITE))
else:
    ps1_src = read(PS1)
    i = ps1_src.find('$suites = @(')
    m = re.search(r'\n\)\s*?\n', ps1_src[i:]) if i >= 0 else None
    last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$", ps1_src[i:i + m.start()])
            if m else None)
    if not last:
        problems.append('%s: could not find the end of $suites' % PS1)
    else:
        j = i + m.start()
        ps1_new = ps1_src[:j] + ',\n' + GATE_NOTE + ps1_src[j:]
        planned[PS1] = (ps1_src, ps1_new)
        report.append('%-28s + %s, after %s' % (PS1, SUITE, last.group(1)))


# ==========================================================================
# SELF-CHECK
# ==========================================================================
for path, (src, text) in sorted(planned.items()):
    rel = os.path.basename(path)
    if path.endswith('.py'):
        # A SUITE THIS ROUND EDITS HAS TO STILL RUN. It is on the gate, so
        # a syntax error in it stops the push either way - but failing here
        # says which file and which line.
        import ast as _ast
        try:
            _ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: the edit does not parse - line %s: %s'
                            % (rel, e.lineno, e.msg))
        continue
    if not path.endswith('.html'):
        continue
    # A DELTA, NOT AN ABSOLUTE. base.html has an unbalanced <table> and <tr>
    # before this round touches it - inside a script template, where no
    # markup rule applies - and asking whether a file balances rather than
    # whether THIS ROUND changed its balance failed base for a fault that is
    # neither new nor mine. Logged, not chased.
    for tag in ('div', 'table', 'thead', 'tbody', 'tr', 'form'):
        d0 = len(re.findall(r'<%s\b' % tag, src)) - src.count('</%s>' % tag)
        d1 = len(re.findall(r'<%s\b' % tag, text)) - text.count('</%s>' % tag)
        if d0 != d1:
            problems.append('%s: <%s> balance moved %d -> %d'
                            % (rel, tag, d0, d1))
    if rel == 'base.html':
        continue
    mk = markup_only(text)
    # THE STANDARD, asserted rather than assumed
    for want in ('<div class="table-container">',
                 'class="table alv-table',
                 'desktop-action-cell', 'mobile-action-bar',
                 'alv-empty-title', 'data-label='):
        if want not in mk:
            problems.append('%s: the rebuilt table has no %s' % (rel, want))
    # every body cell carries its heading
    for m in re.finditer(r'<tbody>(.*?)</tbody>', mk, re.S):
        cells = re.findall(r'<td\b([^>]*)>', m.group(1))
        bare = [c for c in cells
                if 'data-label' not in c
                and 'desktop-action-cell' not in c
                and 'mobile-action-bar' not in c]
        if bare:
            problems.append('%s: %d body cell(s) carry neither a data-label '
                            'nor an action class' % (rel, len(bare)))
    # the old classes are gone from the markup as well as the stylesheet
    for c in DROP_CLASSES.get(rel, []):
        if re.search(r'class="[^"]*(?<![\w-])%s(?![\w-])' % re.escape(c), mk):
            problems.append('%s: the markup still uses .%s' % (rel, c))
    # and the three new names are only used where base now declares them
    for c in ('icon-permissions', 'icon-lock', 'icon-unlock'):
        if c in mk and BASE not in planned and '.icon-permissions' not in \
                read(BASE):
            problems.append('%s: uses .%s and base does not declare it'
                            % (rel, c))


# ==========================================================================
print('\n' + '=' * 74)
print('ADMINISTRATION STAGE E - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
if removed:
    print('\n  The page-local rules the standard makes redundant:')
    for r in removed:
        print('      %s' % r)
print("""
  Kept on purpose, because they style a cell's CONTENT and not the table:
      .user-avatar .user-info .user-name .user-email .user-workspace
      .ws-name .ws-owner-name .ws-owner-username .ws-members
  and the two page containers, which are layout.
""")

if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)

if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)

if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)

for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        write(bak, src)
    write(path, text)

print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
print('         python %s   (the gate)' % PS1)
