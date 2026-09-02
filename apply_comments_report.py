"""apply_comments_report.py - the Comments Report table joins the standard.

    python apply_comments_report.py --check     dry run, writes nothing
    python apply_comments_report.py

Run from the repo root.

WHAT THIS ROUND DOES
--------------------
  .report-table   -> .alv-table, and the page's re-implementation of the
                     table standard (thead fill, th padding and weight, td
                     padding and rule, hover, :last-child reset) is DELETED
                     rather than renamed. Cells gain data-label so base's
                     phone card view can build itself.
  .status-badge   -> .alv-pill, in BOTH places: the template's {% if %} chain
                     and the JS ternary that builds the modal.
  .btn-delete-icon-> .icon-action-btn .icon-delete in a .desktop-action-cell
                     .cell-actions, plus a .mobile-action-bar cols-1 tile.
  the hand-rolled phone card block  -> deleted. 108 lines re-implementing
                     data-label with ::before content literals.
  @media (max-width: 768px)  -> @media screen and (...). The page-local twin
                     of the print leak fixed in base on 1 Sep.

DELIBERATELY NOT TOUCHED: .report-header (the teal gradient banner) and its
.stat-box. Those belong to the banner round, which is sized from a scanner
across 15+ templates rather than from this one page.

HOUSE RULES OBSERVED
--------------------
  * idempotent - every anchor asserted to match EXACTLY ONCE
  * backup to .bak_crb, never overwritten
  * --check writes nothing
  * SELF-CHECK BEFORE WRITING: any failure sys.exits before a byte is
    written, so a half-applied round is not a state this can reach
  * PER-FILE guards, not per-round - see the print round's lesson
"""
import os
import re
import sys

CHECK = '--check' in sys.argv

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
CR = os.path.join(T, 'comments_report.html')

if not os.path.exists(CR):
    sys.exit('! %s not found - run from the repo root' % CR)


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def once(text, needle, what):
    n = text.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, needle[:90]))
    return True


def sub1(text, old, new, what):
    once(text, old, what)
    return text.replace(old, new, 1)


def between(text, start, end, new, what):
    """Replace start..end INCLUSIVE. `start` must be unique; `end` is the
       first occurrence at or after it."""
    once(text, start, what + ' [start]')
    i = text.index(start)
    j = text.index(end, i)
    if j < 0:
        sys.exit('! %s: end marker not found after start' % what)
    return text[:i] + new + text[j + len(end):]


def drop_rule(text, selector, what):
    """Delete the CSS rule whose selector list is EXACTLY `selector`.

       Matched at a line start so `.report-table` never matches inside
       `.report-table thead`, and the closing brace is found by counting
       rather than by taking the first one."""
    pat = re.compile(r'(?m)^[ \t]*' + re.escape(selector) + r'[ \t]*\{')
    hits = list(pat.finditer(text))
    if len(hits) != 1:
        sys.exit('! %s: selector %r matched %d rule openings, expected 1'
                 % (what, selector, len(hits)))
    m = hits[0]
    i, depth, k = m.start(), 1, m.end()
    while depth and k < len(text):
        if text[k] == '{':
            depth += 1
        elif text[k] == '}':
            depth -= 1
        k += 1
    if depth:
        sys.exit('! %s: unbalanced braces after %r' % (what, selector))
    while k < len(text) and text[k] in '\r\n':
        k += 1
    return text[:i] + text[k:]


# ===========================================================================
# comments_report.html
# ===========================================================================
ORIG = read(CR)
# CRLF, every time. Work in LF and put the file's own ending back at the end;
# a multi-line anchor written in a Python triple-quote is LF and will never
# match a \r\n file. This has cost a round three times now.
CRLF = '\r\n' in ORIG
c = ORIG.replace('\r\n', '\n')

if 'class="alv-table"' in c and 'alv-pill-good' in c:
    print('  comments_report.html already patched - nothing to do')
    sys.exit(0)

MARK = '/* ==================== MOBILE (≤768px) ==================== */'
once(c, MARK, 'mobile block marker')
_i = c.index(MARK)
head, mob = c[:_i], c[_i:]

# ------------------------------------------- 1. the page print block, FIRST
# Before the drops, not after: the print block carries its own .status-badge
# rule, so dropping the definition while that one is still there makes the
# selector match twice and the round stops on its own guard. Ask why the
# order matters before changing it.
#
# base already hides .page-action-buttons, .modal, .desktop-action-cell,
# .alv-table .cell-actions, .row-actions and .mobile-action-bar, and already
# outlines .alv-pill in black on transparent. All that is left that base
# cannot know about is the banner's own fill.
S_PRINT_OLD = """@media print {
    .page-action-buttons, .btn-delete-icon, .modal {
        display: none !important;
    }

    .report-header {
        background: #0e7c8b !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    .status-badge {
        border: 1px solid #000 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
}"""
S_PRINT_NEW = """@media print {
    /* WHAT USED TO BE HERE AND IS NOW base's:
         .page-action-buttons, .modal      hidden by base's print block
         .btn-delete-icon                  gone; base hides .desktop-action-cell,
                                           .alv-table .cell-actions, .row-actions
                                           and .mobile-action-bar by name
         .status-badge                     base outlines .alv-pill in black on
                                           transparent, which is the same idea
                                           and survives an empty cyan cartridge

       The banner's fill is the one thing base cannot know about, so it is the
       one thing left. It goes when the banner round takes the banner. */
    .report-header {
        background: #0e7c8b !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
}"""
head = sub1(head, S_PRINT_OLD, S_PRINT_NEW, 'print block')

# --------------------------------------------------------------- 2. CSS/head
# The page re-implemented the table standard. Delete it; do not rename it.
for _sel in ('.report-table',
             '.report-table thead',
             '.report-table th',
             '.report-table td',
             '.report-table tbody tr:hover',
             '.report-table tbody tr:last-child td'):
    head = drop_rule(head, _sel, 'head drop %s' % _sel)

for _sel in ('.status-badge', '.status-resolved', '.status-unresolved',
             '.status-open', '.btn-delete-icon', '.btn-delete-icon:hover'):
    head = drop_rule(head, _sel, 'head drop %s' % _sel)

# Two things ARE this page's, and are put back by name.
S_SCOPED = """/* THE TABLE STANDARD IS base's - .alv-table.

   .report-table lived here and was a full second copy of it: six rules for
   the thead fill, the th padding/weight/colour, the td padding and rule, the
   row hover and the :last-child border reset. All six are in base, and this
   page's copies had drifted from it - an #f8f9fa heading against
   --alv-surface, #dee2e6 and #e9ecef rules against --alv-line and
   --alv-line-soft. Deleted rather than renamed.

   TWO rules are genuinely this page's and stay. */

/* base sets vertical-align: middle, which is right when every cell is one
   line. The Comment column is 35% wide and wraps to three or four; with
   middle, the date sits halfway down beside it and the row loses its top
   line. Top is what this table has always done. */
.alv-table tbody td { vertical-align: top; }

/* Status is centred over a narrow column. base centres headings (.col-center)
   and action cells, but has no rule for a chip column - so it is one rule
   here rather than two inline style attributes, which is what it was. */
.alv-table th.status-cell,
.alv-table td.status-cell { text-align: center; }

/* The em-dash for "this comment has no issue behind it". It was
   style="color: #999" inline; #999 is not a colour this system has. The
   NAME is the point - a reader of the markup can now tell the dash is
   deliberately quiet rather than accidentally grey. */
.status-none { color: var(--alv-ink-faint); }
"""

# Put the scoped block where the deleted rules were: immediately before the
# comment that records the removal of the wash.
head = sub1(head, '/* THE COMMENT WASH IS GONE - 1 Sep.',
            S_SCOPED + '\n/* THE COMMENT WASH IS GONE - 1 Sep.',
            'scoped table rules')

# The accent literal on the clickable comment cell.
head = sub1(head, """.comment-cell:hover {
    color: #0e7c8b;
}""", """.comment-cell:hover {
    color: var(--alv-accent);
}""", 'comment-cell hover token')

# ------------------------------------------------------------- 3. CSS/mobile
# THE PRINT LEAK, page-local twin. A4 portrait is ~718 CSS px of content, so
# an unqualified max-width: 768px block fires on paper.
mob = sub1(mob, '@media (max-width: 768px) {',
           '@media screen and (max-width: 768px) {',
           'mobile block is screen-only')

for _sel in ('.report-table',
             '.report-table thead',
             '.report-table,\n    .report-table tbody,\n    .report-table tr',
             '.report-table tbody tr',
             '.report-table tbody tr:hover',
             '.report-table tbody tr td',
             '.report-table tbody tr td.comment-cell',
             '.report-table tbody tr td.comment-cell::before',
             '.report-table tbody tr td.date-cell::before',
             '.report-table tbody tr td.property-cell::before',
             '.report-table tbody tr td.status-cell::before',
             '.report-table tbody tr td.user-cell::before',
             '.report-table tbody tr td.status-cell,\n    '
             '.report-table tbody tr td.delete-cell',
             '.report-table tbody tr td.delete-cell',
             '.report-table tbody tr td.delete-cell::before',
             '.report-table tbody tr td.delete-cell form',
             '.report-table tbody tr td.delete-cell .btn-delete-icon',
             '.report-table tbody tr td.delete-cell .btn-delete-icon::after'):
    mob = drop_rule(mob, _sel, 'mobile drop %s' % _sel)

# The two orphaned comments those rules sat under.
for _c in ('    /* Status cell text-align reset */\n',
           '    /* Delete cell — full-width button on its own row */\n'):
    if _c in mob:
        mob = mob.replace(_c, '', 1)

S_MOB_NEW = """
    /* THE CARD TITLE IS THE COMMENT, AND A COMMENT IS NOT A TITLE.
       base makes tbody td:first-child 16px/600 with no label, which is right
       on every other migrated page because the first cell there is a NAME -
       Contact Person, Tenant, Property, Date. Here it is the comment itself
       and it can run to a paragraph; at 16px bold that is a wall.

       It stays FIRST, because a card should open with what the row is about.
       It just reads at body weight. The separator rule base draws under the
       first cell is kept - it is exactly what the deleted block drew by hand.

       The extra `tr` is not decoration: base's rule is (0,2,2) and so is
       `.alv-table tbody td.comment-cell`. A tie is decided by source order,
       which is not a thing to rely on across two files. This is (0,2,3). */
    .alv-table tbody tr td.comment-cell {
        /* .comment-cell caps itself at 500px for the desktop column. A card
           is as wide as the phone, so the cap comes off - the deleted block
           reset it too, and dropping the reset would have capped the card on
           a 700px window and looked like a margin bug. */
        max-width: 100%;
        font-size: 14px;
        font-weight: 400;
        color: var(--alv-ink);
    }

    /* The delete needs a <form> around it, and .mobile-action-bar is a grid
       whose children are the tiles - so the form becomes the grid item and
       the button inside it stops filling the cell. Two rules, rather than
       display: contents, which is a cleverness that reads as a typo. */
    .alv-table td.mobile-action-bar > form { display: block; }
    .alv-table td.mobile-action-bar > form .mobile-action-btn {
        width: 100%;
    }

"""
mob = sub1(mob, '    /* Issue link */', S_MOB_NEW + '    /* Issue link */',
           'mobile scoped rules')

c = head + mob

# ------------------------------------------------------------- 4. the markup
c = sub1(c, '<table class="report-table">', '<table class="alv-table">',
         'table class')

c = sub1(c, '<th style="width: 11%; text-align: center;">Status</th>',
         '<th class="status-cell" style="width: 11%">Status</th>',
         'status heading')

c = sub1(c, """                    {% if request.user.is_superuser %}
                    <th style="width: 7%; text-align: center;">Delete</th>
                    {% endif %}""",
         """                    {% if request.user.is_superuser %}
                    <th class="cell-actions" style="width: 7%">Actions</th>
                    {% endif %}""",
         'actions heading')

c = sub1(c, '<td class="date-cell">', '<td class="date-cell" data-label="Date">',
         'date data-label')
c = sub1(c, '<td class="property-cell">',
         '<td class="property-cell" data-label="Property">',
         'property data-label')
c = sub1(c, '<td class="user-cell">',
         '<td class="user-cell" data-label="User">',
         'user data-label')
# The comment cell is the card title, so it takes NO label - see base's
# td:first-child::before { content: none }.
once(c, '<td class="comment-cell" onclick=', 'comment cell')

# The three status badges.
c = sub1(c, """                    <td class="status-cell" style="text-align: center;">
                        {% if item.issue_status %}
                            {% if item.issue_status == "Resolved" %}
                                <span class="status-badge status-resolved">{{ item.issue_status }}</span>
                            {% elif item.issue_status == "Unresolved" or item.issue_status == "Open" %}
                                <span class="status-badge status-unresolved">{{ item.issue_status }}</span>
                            {% else %}
                                <span class="status-badge status-open">{{ item.issue_status }}</span>
                            {% endif %}
                        {% else %}
                            <span style="color: #999;">—</span>
                        {% endif %}
                    </td>""",
         """                    <td class="status-cell" data-label="Status">
                        {% if item.issue_status %}
                            {% if item.issue_status == "Resolved" %}
                                <span class="alv-pill alv-pill-good">{{ item.issue_status }}</span>
                            {% elif item.issue_status == "Unresolved" or item.issue_status == "Open" %}
                                <span class="alv-pill alv-pill-attn">{{ item.issue_status }}</span>
                            {% else %}
                                <span class="alv-pill alv-pill-neutral">{{ item.issue_status }}</span>
                            {% endif %}
                        {% else %}
                            <span class="status-none">—</span>
                        {% endif %}
                    </td>""",
         'status pills')

# The delete cell becomes the house pair: a desktop action cell and a phone bar.
c = sub1(c, """                    {% if request.user.is_superuser %}
                    <td class="delete-cell" style="text-align: center;">
                        <form method="post" action="{% url 'delete_comment' item.comment_id %}" style="display: inline;" onsubmit="return confirm('Are you sure you want to delete this comment? This action cannot be undone.');">
                            {% csrf_token %}
                            <input type="hidden" name="period" value="{{ period }}">
                            <button type="submit" class="btn-delete-icon" title="Delete comment">
                                <i class="fas fa-trash"></i>
                            </button>
                        </form>
                    </td>
                    {% endif %}""",
         """                    {% if request.user.is_superuser %}
                    <td class="desktop-action-cell cell-actions" data-label="">
                        <span class="row-actions">
                            <form method="post" action="{% url 'delete_comment' item.comment_id %}" style="display: inline;" onsubmit="return confirm('Are you sure you want to delete this comment? This action cannot be undone.');">
                                {% csrf_token %}
                                <input type="hidden" name="period" value="{{ period }}">
                                <button type="submit" class="icon-action-btn icon-delete" title="Delete comment">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </form>
                        </span>
                    </td>
                    <td class="mobile-action-bar cols-1" data-label="">
                        <form method="post" action="{% url 'delete_comment' item.comment_id %}" onsubmit="return confirm('Are you sure you want to delete this comment? This action cannot be undone.');">
                            {% csrf_token %}
                            <input type="hidden" name="period" value="{{ period }}">
                            <button type="submit" class="mobile-action-btn">
                                <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                                <span class="mobile-action-label">Delete</span>
                            </button>
                        </form>
                    </td>
                    {% endif %}""",
         'delete cell')

# ----------------------------------------------------------------- 5. the JS
# THE SECOND HOME OF THE SAME MAP. The modal is built in JS, so a status
# chain lives there too - and the two had to be changed together or the
# modal would have kept asking for classes this file no longer defines.
c = sub1(c, """    const statusClass = data.status === 'Resolved' ? 'status-resolved' :
                       (data.status === 'Unresolved' || data.status === 'Open') ? 'status-unresolved' :
                       'status-open';""",
         """    // The same three-way the template makes, and it has to stay the same
    // three-way: this modal and the table behind it show one status each.
    const STATUS_PILL = {
        Resolved: 'alv-pill-good',
        Unresolved: 'alv-pill-attn',
        Open: 'alv-pill-attn'
    };
    const statusClass = STATUS_PILL[data.status] || 'alv-pill-neutral';""",
         'JS status map')

c = sub1(c, '<span class="status-badge ${statusClass}">${data.status}</span>',
         '<span class="alv-pill ${statusClass}">${data.status}</span>',
         'JS status markup')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


def nocomment(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#[^\n]*?#\}', '', t)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, t, flags=re.S)


CC = nocomment(c)

for dead in ('report-table', 'status-badge', 'status-resolved',
             'status-unresolved', 'status-open', 'btn-delete-icon',
             'delete-cell'):
    want(not re.search(r'(?<![\w-])%s(?![\w-])' % dead, CC),
         '%s survives outside a comment' % dead)

want('class="alv-table"' in CC, 'table did not take .alv-table')
# TWICE, not once: the template's {% if %} chain and the JS map that builds
# the modal each name every verdict. attn three times, because Unresolved and
# Open both mean attn and the JS map spells them out as separate keys where
# the template ORs them into one branch.
want(CC.count('alv-pill-good') == 2, 'alv-pill-good: expected 2, got %d'
     % CC.count('alv-pill-good'))
want(CC.count('alv-pill-neutral') == 2, 'alv-pill-neutral: expected 2, got %d'
     % CC.count('alv-pill-neutral'))
want(CC.count('alv-pill-attn') == 3, 'alv-pill-attn: expected 3, got %d'
     % CC.count('alv-pill-attn'))
want('icon-action-btn icon-delete' in CC, 'delete did not take the house icon')
want('mobile-action-bar cols-1' in CC, 'no phone action bar')
want(CC.count('data-label="Date"') == 1
     and CC.count('data-label="Property"') == 1
     and CC.count('data-label="Status"') == 1
     and CC.count('data-label="User"') == 1, 'data-labels missing')
want('@media (max-width: 768px)' not in c,
     'an unqualified max-width block survives - it will print')
want('@media screen and (max-width: 768px)' in c, 'the mobile block vanished')
want(c.count('{% csrf_token %}') == 2, 'csrf token count changed')
want("{% url 'delete_comment' item.comment_id %}" in c,
     'the delete action url was lost')

# The banner is out of scope and must be untouched.
want('.report-header {' in c and 'linear-gradient(135deg, #0e7c8b' in c,
     'the banner was touched - it belongs to its own round')
want('.stat-box {' in c and 'rgba(255, 255, 255, 0.2)' in c,
     'the stat box was touched - it goes with the banner')

# The tint round's work must survive.
want(c.count('alv-tag comment-author') == 2, 'the author chip was lost')

# Braces, and Django comments that would print as prose.
for blk in re.findall(r'<style[^>]*>(.*?)</style>', c, re.S):
    want(blk.count('{') == blk.count('}'), 'unbalanced braces in <style>')
for m in re.finditer(r'\{#', c):
    seg = c[m.start():m.start() + 400]
    want('#}' in seg.split('\n')[0],
         'a {# #} comment spans lines - Django will print it')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for f in FAIL:
        print('   - %s' % f)
    sys.exit(1)

OUT = c.replace('\n', '\r\n') if CRLF else c
print('  comments_report.html  %d -> %d bytes' % (len(ORIG), len(OUT)))

if CHECK:
    print('\n  --check: nothing written.')
    sys.exit(0)

bak = CR + '.bak_crb'
if not os.path.exists(bak):
    with open(bak, 'w', encoding='utf-8', newline='') as f:
        f.write(ORIG)
    print('  backup -> %s' % os.path.basename(bak))
with open(CR, 'w', encoding='utf-8', newline='') as f:
    f.write(OUT)
print('\n  done.')
