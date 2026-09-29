# -*- coding: utf-8 -*-
"""SECTION X, ROUND X1 - COUNTRY CONFIGURATIONS JOINS THE HOUSE

Reported by Demetri on the CRS screens: "This should not be green. Help
button should not be green. The table should not have a green border. The
view modal should comply to our standards."

X0 made this module visible to 33 gates without changing a pixel. X1 is
the first round that changes one, and it takes ONE SCREEN all the way -
list, row actions, empty state and view modal - so the finished shape can
be looked at before it is repeated for Reporting FIs and Submissions.

THE GREEN IS TWO VALUES, AND THIS PAGE IS WHERE THEY STOP
    All eight CRS pages declare the same pair in their own :root -
    --crs-dark: #28a745 and --crs-light: #d4edda - and every green surface
    in the module resolves through one of them. On this page they paint
    .crs-panel's 3px border and tinted fill, .view-section-h in the modal,
    and the empty-state icon.

    The panel does not get retoned. It gets DELETED. Measured on
    properties, suppliers and tenant: a house list page has NO outer panel
    at all - .table-container and .alv-table sit on the page background.
    So "the table should not have a green border" has no teal answer; the
    house has nothing there to paint.

    That leaves .view-section-h, which base does not own. It is kept and
    moved onto var(--alv-accent), after which :root has no readers and
    goes too. No hex, no keyword, no local palette.

WHY THE HELP BUTTON IS GREEN AND THE BACK BESIDE IT IS NOT
    Both carry btn-success. Back also carries .action-back, which base
    owns, and base's style block is read AFTER Bootstrap's CDN link - so
    at equal specificity base wins and Back looks right. Help carries
    `action-icon`, which matches NOTHING: base owns .icon-action-btn and
    .mobile-action-icon, and has never had a class by that name. With no
    house rule to beat it, Bootstrap's #28a745 paints the button.

    So the defect is a misspelling that has been invisible for as long as
    it has existed, and the fix is the house Help button as the only two
    pages that have one already write it: `btn action-secondary`.

WHAT ELSE STOPS BEING HAND-ROLLED
    .crs-table            -> .table-container + .alv-table
    td::before per nth-child -> data-label, which is what base's mobile
                             card layout reads. The page had five
                             hand-numbered content rules that silently
                             mislabel every column the day one is inserted.
    .action-btn/.btn-view/
    .btn-edit/.btn-delete -> .icon-action-btn + .icon-view/-edit/-delete
    (no mobile bar at all) -> .mobile-action-bar, so a phone gets the same
                             three actions as every other list in the
                             system rather than three 38px squares
    .status-active/-inactive -> .alv-pill alv-pill-good / -neutral
    .crs-empty            -> .alv-empty + -title + -hint
    modal-header bg-info  -> .alv-modal-head
    modal Close btn-secondary -> .action-secondary

    And the title loses both `<center>` and the brand prefix, which is the
    standard passport_management already wears.

NOT DONE HERE
    The message block at the top of the page hand-rolls a Bootstrap alert
    and an inline setTimeout to dismiss it. Every list page in the system
    does the same thing, and settings.py has no MESSAGE_TAGS, so 295 error
    messages render unstyled. That is the message-bar round, it is
    system-wide, and folding it in here would hide it inside a CRS diff.

Backups: .bak_crscountry. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crscountry'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    """Write the backup and PROVE it is a copy (lesson 46)."""
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('X1: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70 - an anchor written with \\n matches nothing in a CRLF
    file, and country_list.html is CRLF."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def bare(s):
    """Selector with CSS comments stripped - lesson 21."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def swap(path, text, was, now, why):
    a, b = eol(path, was), eol(path, now)
    if text.count(a) != 1:
        raise SystemExit('X1: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
MARK = [
    # --- the title: no <center>, no brand prefix
    ('<h2 class="page-title-h2"><center>ALIVENTE ONLINE - '
     'CRS COUNTRY CONFIGURATIONS</center></h2>',
     '<h2 class="page-title-h2">CRS COUNTRY CONFIGURATIONS</h2>',
     'the title'),

    # --- the bar
    ('<a href="{% url \'crs:country_add\' %}" '
     'class="btn btn-info action-primary">',
     '<a href="{% url \'crs:country_add\' %}" class="btn action-primary" '
     'role="button">',
     'Add Country'),
    ('  <button type="button" class="btn btn-success btn-sm action-icon"\r\n'
     '        data-toggle="modal" '
     'data-target="#crs_country_configurationsHelpModal" aria-label="Help">'
     '\r\n    <i class="fas fa-question-circle"></i>'
     '<span class="action-back-label"> Help</span>\r\n  </button>',
     '  <button type="button" class="btn action-secondary"\r\n'
     '        data-toggle="modal" '
     'data-target="#crs_country_configurationsHelpModal" aria-label="Help">'
     '\r\n    <i class="fas fa-question-circle"></i> Help\r\n  </button>',
     'Help'),
    ('class="btn btn-success action-back"',
     'class="btn action-back"',
     'Back'),

    # --- the panel goes, and the table becomes the house table
    ('<!-- Single Panel -->\r\n'
     '<div class="crs-panel-container">\r\n'
     '  <div class="crs-panel">\r\n'
     '\r\n'
     '    {% if countries %}\r\n'
     '    <div class="crs-table">\r\n'
     '      <table>',
     '<!-- Countries table (desktop) / card list (mobile) -->\r\n'
     '<div class="table-container">\r\n'
     '  <table class="table alv-table crs-country-table">',
     'the panel and the table open'),

    ('          <tr>\r\n'
     '            <th>Code</th>\r\n'
     '            <th>Country</th>\r\n'
     '            <th>Status</th>\r\n'
     '            <th>Schema</th>\r\n'
     '            <th>Last Updated</th>\r\n'
     '            <th>Actions</th>\r\n'
     '          </tr>',
     '      <tr>\r\n'
     '        <th style="text-align: left; width: 10%">Code</th>\r\n'
     '        <th style="width: 30%">Country</th>\r\n'
     '        <th style="width: 14%">Status</th>\r\n'
     '        <th style="width: 12%">Schema</th>\r\n'
     '        <th style="width: 20%">Last Updated</th>\r\n'
     '        <th class="desktop-action-cell cell-actions" '
     'style="width: 14%">Actions</th>\r\n'
     '      </tr>',
     'the head'),
]

# The row. Rewritten whole, because every cell gains a data-label and the
# actions cell becomes two - one for the desktop, one for the phone.
ROW_WAS = """          <tr>
            <td><strong>{{ country.country_code }}</strong></td>
            <td>{{ country.country_name }}</td>
            <td>
              {% if country.is_active %}
                <span class="status-active"><i class="fas fa-circle"></i> Active</span>
              {% else %}
                <span class="status-inactive"><i class="fas fa-circle"></i> Inactive</span>
              {% endif %}
            </td>
            <td>{{ country.oecd_version }}</td>
            <td>{{ country.updated_at|date:"d M Y H:i" }}</td>
            <td>
              <div class="row-actions">
                <button type="button" class="action-btn btn-view" title="View"
                        onclick="viewCountry({{ country.pk }})">
                  <i class="fas fa-eye"></i>
                </button>
                {% if perms.auth.can_edit_crs %}
                <a href="{% url 'crs:country_edit' country.pk %}"
                   class="action-btn btn-edit" title="Edit">
                  <i class="fas fa-pencil-alt"></i>
                </a>
                <button type="button" class="action-btn btn-delete" title="Delete"
                        onclick="confirmCountryDelete({{ country.pk }}, '{{ country.country_code }} — {{ country.country_name|escapejs }}')">
                  <i class="fas fa-trash"></i>
                </button>
                {% endif %}
              </div>
            </td>
          </tr>"""

ROW_NOW = """        <tr>
          <td data-label="Code" style="text-align: left"><strong>{{ country.country_code }}</strong></td>
          <td data-label="Country">{{ country.country_name }}</td>
          <td data-label="Status">
            {% if country.is_active %}
              <span class="alv-pill alv-pill-good">Active</span>
            {% else %}
              <span class="alv-pill alv-pill-neutral">Inactive</span>
            {% endif %}
          </td>
          <td data-label="Schema">{{ country.oecd_version }}</td>
          <td data-label="Last Updated">{{ country.updated_at|date:"d M Y H:i" }}</td>

          <!-- Desktop actions: one cell, three buttons -->
          <td class="desktop-action-cell cell-actions">
            <span class="row-actions">
              <button type="button" class="icon-action-btn icon-view" title="View Country Configuration"
                      onclick="viewCountry({{ country.pk }})">
                <i class="fas fa-eye"></i>
              </button>
              {% if perms.auth.can_edit_crs %}
                <a href="{% url 'crs:country_edit' country.pk %}"
                   class="icon-action-btn icon-edit" title="Edit Country Configuration">
                  <i class="fas fa-pencil-alt"></i>
                </a>
                <button type="button" class="icon-action-btn icon-delete" title="Delete Country Configuration"
                        onclick="confirmCountryDelete({{ country.pk }}, '{{ country.country_code }} — {{ country.country_name|escapejs }}')">
                  <i class="fas fa-trash"></i>
                </button>
              {% else %}
                <span class="icon-action-btn icon-disabled" title="No edit permission">
                  <i class="fas fa-pencil-alt"></i>
                </span>
                <span class="icon-action-btn icon-disabled" title="No delete permission">
                  <i class="fas fa-trash"></i>
                </span>
              {% endif %}
            </span>
          </td>

          <!-- Mobile-only action bar (hidden on desktop) -->
          <td class="mobile-action-bar">
            <button type="button" class="mobile-action-btn" onclick="viewCountry({{ country.pk }})">
              <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
              <span class="mobile-action-label">View</span>
            </button>
            {% if perms.auth.can_edit_crs %}
              <a href="{% url 'crs:country_edit' country.pk %}" class="mobile-action-btn">
                <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
                <span class="mobile-action-label">Edit</span>
              </a>
              <button type="button" class="mobile-action-btn"
                      onclick="confirmCountryDelete({{ country.pk }}, '{{ country.country_code }} — {{ country.country_name|escapejs }}')">
                <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                <span class="mobile-action-label">Delete</span>
              </button>
            {% else %}
              <span class="mobile-action-btn mobile-action-disabled">
                <i class="fas fa-pencil-alt mobile-action-icon"></i>
                <span class="mobile-action-label">Edit</span>
              </span>
              <span class="mobile-action-btn mobile-action-disabled">
                <i class="fas fa-trash mobile-action-icon"></i>
                <span class="mobile-action-label">Delete</span>
              </span>
            {% endif %}
          </td>
        </tr>"""

# The close of the table, the empty state, and the two wrappers that go.
TAIL_WAS = """      </table>
    </div>
    {% else %}
    <div class="crs-empty">
      <i class="fas fa-globe"></i>
      <p>No country configurations yet.</p>
      <small>Click "Add Country" to create one.</small>
    </div>
    {% endif %}

  </div>
</div>"""

TAIL_NOW = """  </table>

  {% if not countries %}
    {# An empty tbody looks exactly like a failed load. #}
    <div class="alv-empty">
      <i class="fas fa-globe"></i>
      <div class="alv-empty-title">No country configurations yet</div>
      <div class="alv-empty-hint">
        Add your first country to tell the system how its files are built.
      </div>
    </div>
  {% endif %}
</div>"""

MARK2 = [
    # {% if countries %} wrapped the table; the house puts the empty state
    # INSIDE the container, after the table, and tests emptiness there.
    ('        <tbody>\r\n          {% for country in countries %}',
     '    <tbody>\r\n      {% for country in countries %}',
     "the body's open"),
    ('          {% endfor %}\r\n        </tbody>',
     '      {% endfor %}\r\n    </tbody>',
     "the body's close"),

    # --- the view modal
    ('<div class="modal-header bg-info text-white">',
     '<div class="modal-header alv-modal-head">',
     "the modal's header"),
    ('<button type="button" class="btn btn-secondary" '
     'data-dismiss="modal">Close</button>',
     '<button type="button" class="btn action-secondary" '
     'data-dismiss="modal">Close</button>',
     "the modal's Close"),
]

# --- the CSS this page stops needing, because base already owns it.
# Named exactly. A pattern would also take .view-row and .view-code, which
# base does not own and this round keeps.
DEAD = [
    ':root',
    '.page-title-h2',
    '.page-action-buttons',
    '.page-action-buttons .action-primary',
    '.page-action-buttons .action-back',
    '.action-back-label',
    '.crs-panel-container',
    '.crs-panel',
    '.crs-table',
    '.crs-table table',
    '.crs-table thead th',
    '.crs-table tbody td',
    '.crs-table tbody tr:last-child td',
    '.crs-table tbody tr:hover',
    '.crs-table table, .crs-table thead, .crs-table tbody, .crs-table tr, '
    '.crs-table td',
    '.crs-table thead',
    '.crs-table tbody tr',
    '.crs-table tbody td::before',
    ".crs-table tbody td:nth-child(1)::before",
    ".crs-table tbody td:nth-child(2)::before",
    ".crs-table tbody td:nth-child(3)::before",
    ".crs-table tbody td:nth-child(4)::before",
    ".crs-table tbody td:nth-child(5)::before",
    '.crs-table tbody td:last-child',
    '.crs-table tbody td:last-child::before',
    '.status-active',
    '.status-active i',
    '.status-inactive',
    '.status-inactive i',
    '.row-actions',
    '.action-btn',
    '.action-btn:hover',
    '.btn-view',
    '.btn-edit',
    '.btn-delete',
    '.crs-empty',
    '.crs-empty i',
    '.crs-empty p',
    '.crs-empty small',
]

# Kept, with the reason. base does not own these - they are the view
# modal's own furniture - so they stay, retoned.
KEPT = ['.view-row', '.view-row label', '.view-section-h',
        '.view-section-h:first-child', '.view-code']

# The rules base does NOT own, which therefore survive - onto tokens.
# Every substitution below was measured; the deltas are stated so a later
# hand can see what was traded and for what.
RETONE = [
    # #495057 -> --alv-ink-strong #41535c. Distance 16 of 765; contrast on
    # the modal ground 7.76:1 -> 7.61:1. Invisible, and ink-strong is the
    # house's colour for exactly this - a bold label beside a value.
    ('  .view-row label { font-weight: 600; color: #495057; '
     'margin-right: 8px; margin-bottom: 0; }',
     '  .view-row label { font-weight: 600; color: var(--alv-ink-strong); '
     'margin-right: 8px; margin-bottom: 0; }',
     '.view-row label'),

    # The code chip. Three literals, three decisions:
    #
    #   background #f8f9fa -> --alv-surface        exact, distance 0
    #   border     #e9ecef -> --alv-line           distance 15
    #       --alv-surface-deep is #e9ecef exactly, so it would have been a
    #       zero-pixel swap - but it is a SURFACE token, and this is a
    #       BORDER. Standard 3.1 says a colour means something. Took the
    #       line token and the 15-unit change with it.
    #   colour     #c7254e -> --alv-ink            distance 199
    #       This one is visible: a crimson becomes near-black. #c7254e is
    #       Bootstrap 3's inline-code colour, carried in by copy and
    #       meaning nothing in this system - and the house has no code
    #       component to appeal to. --alv-accent-ink was the alternative
    #       and was rejected: accent means primary action and selection,
    #       and a template string is neither, so it would be a semantic
    #       token used for decoration - the thing 3.1 names last. The chip
    #       is already distinguished by its ground, its border and its
    #       typeface. Contrast on that ground improves, 5.24:1 -> 12.29:1.
    ("""  .view-code {
    display: inline-block; padding: 2px 8px;
    background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px;
    font-family: Consolas, monospace; font-size: 12px;
    color: #c7254e; word-break: break-all; max-width: 100%;
  }""",
     """  .view-code {
    display: inline-block; padding: 2px 8px;
    background: var(--alv-surface); border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    font-family: Consolas, monospace; font-size: 12px;
    color: var(--alv-ink); word-break: break-all; max-width: 100%;
  }""",
     '.view-code'),

    ("""  .view-section-h {
    margin: 20px 0 10px 0; padding-bottom: 6px;
    border-bottom: 2px solid #e9ecef;
    font-size: 13px; font-weight: 700; text-transform: uppercase;
    color: var(--crs-dark); letter-spacing: 0.5px;
  }""",
     """  /* The modal's section headings. base does not own this component, so
     the rule stays - but the colour comes from the house accent rather
     than from a --crs-dark that no longer exists, and the rule below it
     from --alv-line rather than a hex. */
  .view-section-h {
    margin: 20px 0 10px 0; padding-bottom: 6px;
    border-bottom: 2px solid var(--alv-line);
    font-size: 13px; font-weight: 700; text-transform: uppercase;
    color: var(--alv-accent); letter-spacing: 0.5px;
  }""",
     '.view-section-h'),
]

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X1 - COUNTRY CONFIGURATIONS JOINS THE HOUSE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs', 'country_list.html')
if not os.path.isfile(path):
    raise SystemExit('X1: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'alv-table' in text:
    print('  %-30s already on the house table' % 'country_list')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

for was, now, why in MARK:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('country_list', why))

text = swap(path, text, ROW_WAS, ROW_NOW, 'the row')
print('  %-30s %s' % ('country_list', 'the row - data-label, house icons, '
                      'a mobile bar'))
text = swap(path, text, TAIL_WAS, TAIL_NOW, 'the table close and the empty')
print('  %-30s %s' % ('country_list', 'the empty state, inside the '
                      'container'))

for was, now, why in MARK2:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('country_list', why))

for was, now, why in RETONE:
    text = swap(path, text, was, now, why)
    print('  %-30s %s onto tokens' % ('country_list', why))

# ---- the dead rules
gone = 0
blocks = [(m.start(1), m.end(1)) for m in STYLE.finditer(text)]
for s, e in reversed(blocks):
    body, last, out = text[s:e], 0, []
    for m in RULE.finditer(body):
        if bare(m.group(1)) not in DEAD:
            continue
        st = m.start() + (len(m.group(1)) - len(m.group(1).lstrip()))
        hd = body.rfind('\n', 0, st) + 1
        if body[hd:st].strip():
            hd = st
        en = m.end()
        # Lesson from H7: the tail trim must consume \r too, or a CRLF
        # file is left with a stray carriage return as a blank line.
        while en < len(body) and body[en] in ' \t\r':
            en += 1
        if en < len(body) and body[en] == '\n':
            en += 1
        if hd < last:
            continue
        out.append(body[last:hd])
        last, gone = en, gone + 1
    out.append(body[last:])
    text = text[:s] + ''.join(out) + text[e:]
print('  %-30s - %d rule(s) base already owns' % ('country_list', gone))

# ==========================================================================
# GATES, before anything is written.
# ==========================================================================
css = '\n'.join(STYLE.findall(text))
names = [bare(m.group(1)) for m in RULE.finditer(css)]

for d in DEAD:
    if d in names:
        raise SystemExit('X1: %s survives' % d)
for k in KEPT:
    if k not in names:
        raise SystemExit('X1: %s was removed - this round keeps it, and the '
                         'reason is in the docstring' % k)

# No local palette, no hex, no keyword - the whole point of the round.
#
# LESSON 21, A THIRD TIME, IN A PLACE IT HAD NOT BITTEN BEFORE. The first
# draft of this gate read `if '--crs-' in text`, and it failed - on the
# CSS COMMENT this round writes above .view-section-h, which says the
# colour no longer comes from a --crs-dark that no longer exists. A
# comment naming a retired token is exactly the documentation this
# programme wants; it is not a reader of it. Every comparison against CSS
# strips comments first, and that now includes this one.
live = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)
if '--crs-' in live:
    raise SystemExit('X1: a --crs-* token still has a reader: %s'
                     % re.findall(r'--crs-\w+', live)[:4])
hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b',
                              re.sub(r'/\*.*?\*/', ' ', css, flags=re.S))))
if hexes:
    raise SystemExit('X1: %d hex(es) left in the page stylesheet: %s'
                     % (len(hexes), hexes))

# The markup must not keep a name base does not own.
mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
# A SUBSTRING TEST ON A CLASS NAME IS NOT A TEST FOR THAT CLASS, and this
# gate proved it on itself: `'action-icon' in mk` fired on
# `mobile-action-icon`, which is base's own class and is exactly what the
# round ADDS. The same shape as H7's `color` matching inside
# `background-color`. Match the whole class token.
for name in ('crs-panel', 'crs-table', 'crs-empty', 'action-icon',
             'btn-success', 'btn-info', 'status-active', 'status-inactive',
             'action-btn', 'btn-view', 'btn-edit', 'btn-delete', 'bg-info'):
    if re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', mk):
        raise SystemExit('X1: the class %r survives in the markup' % name)
# SCOPED TO THE HEADING, and the first draft was not - it failed on the
# <center> inside the MESSAGE BLOCK, which this round deliberately does
# not touch (see NOT DONE HERE). The standard test_heading_components
# states is that no HEADING wraps itself in a center element, so that is
# what is asserted. The message block's centre goes with the message-bar
# round, together with the other 87 pages that write the same thing.
for h in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mk, re.S):
    if '<center>' in h:
        raise SystemExit('X1: a heading still wraps itself in <center>: %s'
                         % ' '.join(h.split())[:70])
if mk.count('<center>') != 1:
    raise SystemExit('X1: expected exactly the message block\'s one '
                     '<center> to remain, found %d' % mk.count('<center>'))

# The house table, spelled the house way.
if mk.count('class="table alv-table crs-country-table"') != 1:
    raise SystemExit('X1: the table does not wear .alv-table exactly once')
if mk.count('<div class="table-container">') != 1:
    raise SystemExit('X1: there is not exactly one .table-container')
labels = re.findall(r'data-label="([^"]+)"', mk)
if labels != ['Code', 'Country', 'Status', 'Schema', 'Last Updated']:
    raise SystemExit('X1: the data-labels are %r, not the five columns'
                     % labels)
if mk.count('class="desktop-action-cell cell-actions"') != 2:
    raise SystemExit('X1: the actions column needs the header cell and the '
                     'body cell, and has %d'
                     % mk.count('class="desktop-action-cell cell-actions"'))
if mk.count('class="mobile-action-bar"') != 1:
    raise SystemExit('X1: there is no mobile action bar')
for icon in ('icon-view', 'icon-edit', 'icon-delete'):
    if 'icon-action-btn %s' % icon not in mk:
        raise SystemExit('X1: the row has no %s' % icon)
if 'alv-pill-good' not in mk or 'alv-pill-neutral' not in mk:
    raise SystemExit('X1: the status column is not on .alv-pill')
if 'alv-modal-head' not in mk:
    raise SystemExit('X1: the view modal did not get the house header')
if 'btn action-secondary' not in mk:
    raise SystemExit('X1: Help is not on the house secondary')
if mk.count('alv-empty') < 3:
    raise SystemExit('X1: the empty state is not the house component')
if len(text) >= len(before):
    raise SystemExit('X1: the page did not shrink')

print('-' * 74)
print('  1 changed  (%+d chars)' % (len(text) - len(before)))
print('  %-30s %s' % ('', 'and this page is now one of the %d templates'
                      % len(alv_tree.templates())))
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
