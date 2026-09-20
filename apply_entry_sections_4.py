# -*- coding: utf-8 -*-
"""apply_entry_sections_4.py - the five Projects entry screens.

    python apply_entry_sections_4.py --check
    python apply_entry_sections_4.py
    python test_entry_sections.py
    python Push-PendingChanges.ps1

THE LAST OF THE ENTRY-SECTIONS WORK. Held since 19 Sep for the rollup, which
shipped and was backfilled on production on 20 Sep, so the auto-calculated
branches on these screens now display values that are really stored.

WHAT THE STRUCTURE TURNED OUT TO BE, measured against the live tree rather
than remembered:

  * NOT ONE OF THE FIVE USES .form-row. Zero, across all five. They lay out
    with Bootstrap's plain .row and col-md-*. Pushes 2 and 3 found a
    section's starting point by locating the .form-row holding a named
    field; that step has nothing to find here, so every anchor in this round
    is a <div class="row"> or a Django tag, and each is asserted to match
    exactly once.

  * THE CONDITIONALS SIT INSIDE THE ROWS, NOT ACROSS THEM. The 20 Sep survey
    feared the opposite and scoped the round around it. On
    project_tasks_edit the row wraps the {% if %}:

        <div class="row">
        {% if not task.parent_task %}  start, expected  (disabled)
        {% else %}                     start, expected  {% endif %}
        </div>

    so a title placed before the row renders for a parent AND a subtask.
    Only ONE title in this round goes inside a conditional - Completion &
    Assignment, inside {% if task.parent_task %}, because a parent task has
    no actual completion date, no assignee and no progress percentage of its
    own. A heading rendering for a parent with nothing under it would be
    worse than no heading.

  * PROJECTS PUTS THE ICON ON THE FIELD LABEL. 43 of its 45 labels do.
    Counted across all 28 form-posting screens, 121 of 643 labels carry an
    icon - but the entry screens this programme has standardised
    (customer_invoice_form, properties_add/_edit, tenant_add/_edit,
    cash_receipt_add) carry ZERO. Everywhere else the icon belongs to the
    section title. Adding titles without stripping these would give every
    panel an icon on its heading and an icon on every field beneath it.
    All 43 are the same shape, asserted before anything is written.

  * BOTH EDIT SCREENS DIVIDE ENGLISH FROM GREEK WITH A BOOTSTRAP TAB BAR,
    reading EN English / GR Ellinika (Greek). No section title goes inside a
    tab pane: the tab bar is already the divider, and a Greek Translation
    heading inside the Greek pane is word for word the redundancy removed
    from three modals in the 20 Sep fix round. Both edit screens are
    titled below the tabs only.

  * EACH SCREEN IS ONE .form-card. Push 3's rule for a modal body applies:
    where the container is already a box, A SECTION IS A TITLE AND NOT A
    CARD. Nothing is rebuilt into panels, so no field can be lost.

ONE FIELD MOVES, AND IT IS NAMED. project_subtasks_add renders Subtask
Description alone in the last row, after Assigned To. It moves up to
directly after name/priority/status, which is where projects_add and
project_tasks_add already put their description, and which turns four
sections into three. Everything else keeps its position, and the self-check
requires the unnamed fields to be in exactly the order they were.

NOT IN THIS ROUND, both logged:

  * The `Quick Actions:` label on both edit screens has no <strong>. It is
    off the label standard and it was already off it - debt this round
    uncovers rather than causes. It is also not a field label: it heads two
    buttons. Fixing it means deciding what it should be, which is a
    decision, not a patch.

  * project_subtasks_add marks Actual Completion Date REQUIRED on a screen
    that CREATES a subtask. That reads like a real fault, but it is
    behaviour and this round is layout.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_sect4'
TAG, CLS = 'h3', 'form-section-title'
SUITE = 'test_entry_sections.py'
PS1 = 'Push-PendingChanges.ps1'

report, problems = [], []


def read(p):
    """Text as LF, and REMEMBER WHAT THE FILE ACTUALLY USED.

    A PATCHER THAT CHANGES FOUR LINES MUST NOT REWRITE THE FILE. Python's
    text mode translates CRLF to LF on the way in, and writing back with
    newline='' then emits LF - so a tool that touched one label silently
    converted the whole file and put every line of it in the commit. It
    happened: properties_add/_edit, tenant_add/_edit, test_entry_sections.py
    and Show-MobileForm.py are all-LF now and were CRLF before, and the
    five Projects templates are still CRLF. Whatever a file uses, it keeps
    it - the diff is then the change, and a reviewer can see it."""
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


CRLF = {}


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def markup_only(text):
    """<script> and <style> bodies blanked to spaces, offsets preserved."""
    out = list(text)
    for m in re.finditer(r'<(script|style)[^>]*>(.*?)</\1>', text, re.S):
        for i in range(m.start(2), m.end(2)):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def indent_at(text, pos):
    ls = text.rfind('\n', 0, pos) + 1
    return re.match(r'[ \t]*', text[ls:]).group(0)


def heading(icon, title, pad):
    return ('%s<%s class="%s"><i class="fas fa-%s"></i> %s</%s>\n'
            % (pad, TAG, CLS, icon, title, TAG))


def fields(text):
    """Every control's name=, in order. A hidden input is data - push 2
    learned that by deleting two of them."""
    out = []
    for m in re.finditer(r'<(input|select|textarea)\b([^>]*)>',
                         markup_only(text), re.I):
        if re.search(r'type\s*=\s*["\'](?:submit|button|reset|image)["\']',
                     m.group(2), re.I):
            continue
        n = re.search(r'\bname\s*=\s*["\']([^"\']+)', m.group(2))
        out.append(n.group(1) if n else '-')
    return out


FILES = ['projects/projects_add.html',
         'projects/project_tasks_add.html',
         'projects/projects_edit.html',
         'projects/project_subtasks_add.html',
         'projects/project_tasks_edit.html']

# --------------------------------------------------------------------------
# THE TITLES.  Each entry is (icon, title, anchor_regex).  The anchor is
# asserted to match EXACTLY ONCE in the file, and the title is inserted on
# its own line immediately before it, at the anchor's own indent.
#
# An anchor is a ROW or a DJANGO TAG, never a field, because these screens
# have no .form-row and because a field can appear twice.
# --------------------------------------------------------------------------
# HOW AN ANCHOR IS FOUND, and why not with a lookahead.
#
# The first draft wrote  <div class="row">(?=(?:.*\n)*?id="task_start_date")
# and it matched THREE rows on project_subtasks_add, because the lookahead
# is free to scan to the end of the file: every row before the field
# satisfies it. The guard caught that, which is the only reason this
# comment is not a bug report.
#
# So the anchor is computed, not matched: find the field, then take the
# LAST row that opens before it. That is one position by construction, and
# it is the row the field is actually in.
# A ROW IS NOT ALWAYS `<div class="row">`. The first draft matched that
# literal and placed Completion & Assignment two rows too high on
# project_subtasks_add, because the row it belongs to is
#
#     <div class="row" id="actualCompletionRow" style="display: none;">
#
# and on project_tasks_edit the same row carries a Django tag inside the
# open tag and spans two lines. Neither was in the list of rows at all, so
# the anchor silently fell back to the row before. `[^>]*` crosses a
# newline, because it is a negated character class and not a dot.
#
# NOTE, recorded rather than acted on: that row is hidden by default and
# revealed by script when the status is Completed. The heading above it
# still has Assigned To under it in every state, so it is never a heading
# with nothing beneath it - which is the reason the last section on
# project_tasks_edit sits inside a conditional.
ROW_OPEN = re.compile(r'[ \t]*<div class="row"[^>]*>\n')


def close_of(mk, after_open):
    """End of the <div> whose opening tag ends at `after_open`.

    A REGEX CANNOT FIND THE END OF A NESTED BLOCK, and the first draft of
    this round proved it: it matched the description row lazily up to the
    first </div> after the field - the one closing .form-group - and moved
    two thirds of a row. THE DIV BALANCE CHECK PASSED, because a move takes
    the same tags out of one place and puts them into another: what was cut
    short here was left behind there, and the totals never moved. A move is
    invisible to counting."""
    depth, i = 1, after_open
    for m in re.finditer(r'<div\b[^>]*>|</div>', mk[i:]):
        depth += 1 if m.group(0) != '</div>' else -1
        if depth == 0:
            return i + m.end()
    return None


def row_span(mk, field):
    """(start, end) of the WHOLE <div class="row"> ... </div> holding the
    field, its opening indent included and its trailing newline too."""
    span, why = row_before(mk, field)
    if span is None:
        return None, why
    a, b = span
    end = close_of(mk, b)
    if end is None:
        return None, 'the row holding id=%r never closes' % field
    if mk[end:end + 1] == '\n':
        end += 1
    return (a, end), None


def row_before(mk, field):
    """(start, end) of the <div class="row"> the field sits in.

    A field id may appear TWICE - project_tasks_edit renders five controls
    in an auto-calculated branch and an editable one - and that is fine
    here: both live in the SAME row, because the row wraps the {% if %}.
    Asserting that is the point of the `same_row` check below."""
    hits = [m.start() for m in re.finditer(r'id="%s"' % re.escape(field), mk)]
    if not hits:
        return None, 'no control has id=%r' % field
    rows = [m for m in ROW_OPEN.finditer(mk)]
    opens = [m for m in rows if m.start() < hits[0]]
    if not opens:
        return None, 'no <div class="row"> opens before id=%r' % field
    chosen = opens[-1]
    # every occurrence of the field must be in this same row - if a second
    # one is further down the file it is a different row and the title
    # would be in the wrong place for half the renders.
    later = [m for m in rows if m.start() > chosen.start()]
    end = later[0].start() if later else len(mk)
    stray = [h for h in hits if not (chosen.start() < h < end)]
    if stray:
        return None, ('id=%r appears %d time(s) and not all in one row'
                      % (field, len(hits)))
    return (chosen.start(), chosen.end()), None


def if_block_holding(mk, cond, field):
    """The {% if cond %} whose block contains the field, asserted unique.

    project_tasks_edit has {% if not task.parent_task %} as well as
    {% if task.parent_task %}; the first draft matched both and stopped.
    Naming the field the block must contain is what separates them."""
    out = []
    for m in re.finditer(re.escape(cond).replace('\\ ', r'\s+'), mk):
        depth, i, end = 1, m.end(), None
        for k in re.finditer(r'\{%\s*(if|endif)\b[^%]*%\}', mk[i:]):
            depth += 1 if k.group(1) == 'if' else -1
            if depth == 0:
                end = i + k.start()
                break
        if end is not None and ('id="%s"' % field) in mk[i:end]:
            out.append(m)
    if len(out) != 1:
        return None, ('%s containing id=%r matched %d time(s)'
                      % (cond, field, len(out)))
    return (out[0].start(), out[0].end()), None


# --------------------------------------------------------------------------
# THE TITLES.  (icon, title, kind, target)
#
#   'row'      the title goes BEFORE the row the named field sits in
#   'comment'  before a literal string already in the file
#   'in_if'    just INSIDE the {% if %} whose block holds the named field
# --------------------------------------------------------------------------
SECTIONS = {
    'projects/projects_add.html': [
        ('project-diagram', 'Project', 'row', 'project_name')],
    'projects/project_tasks_add.html': [
        ('tasks', 'Task', 'row', 'task_name')],

    # BELOW THE TABS ONLY. The auto-calculated block is outside
    # .tab-content, and the comment in front of it is this file's own.
    'projects/projects_edit.html': [
        ('calendar-check', 'Schedule &amp; Status', 'comment',
         '<!-- Auto-calculated fields -->')],

    'projects/project_subtasks_add.html': [
        ('tasks', 'Subtask', 'row', 'task_name'),
        ('calendar-alt', 'Schedule &amp; Cost', 'row', 'task_start_date'),
        ('user-check', 'Completion &amp; Assignment', 'row',
         'task_actual_completion_date')],

    'projects/project_tasks_edit.html': [
        ('calendar-alt', 'Schedule', 'row', 'task_start_date'),
        ('euro-sign', 'Cost', 'row', 'task_budgeted_cost'),
        # THE ONE TITLE INSIDE A CONDITIONAL. Its three fields do not exist
        # for a parent task, so the heading must not render for one.
        ('user-check', 'Completion &amp; Assignment', 'in_if',
         'task_actual_completion_date')],
}

IF_COND = '{% if task.parent_task %}'

# The title that must end up INSIDE a conditional, named here so the suite
# and the self-check can both assert it rather than infer it.
INSIDE_IF = {'projects/project_tasks_edit.html':
             [('Completion &amp; Assignment', IF_COND)]}

# --------------------------------------------------------------------------
# THE MOVE - one field, named.
# --------------------------------------------------------------------------
MOVES = {'projects/project_subtasks_add.html': ['task_description']}

planned = {}


def strip_label_icons(rel, text):
    """<label ...><i class="fas fa-x"></i> <strong>  ->  <label ...><strong>

    Every icon-bearing label on these five screens is this exact shape; it
    is counted before and after, and a label that does not match is a
    problem rather than something to be clever about."""
    mk = markup_only(text)
    labels = re.findall(r'<label\b[^>]*>.*?</label>', mk, re.S)
    with_icon = [l for l in labels if re.search(r'<i\s', l)]
    pat = re.compile(r'(<label\b[^>]*>)(\s*)<i\s+class="[^"]*"></i>[ \t]*'
                     r'(\s*)(<strong>)', re.S)
    odd = [re.sub(r'\s+', ' ', l)[:90] for l in with_icon
           if not pat.match(l)]
    if odd:
        problems.append('%s: %d icon label(s) are not the expected shape - %s'
                        % (rel, len(odd), odd[0]))
        return text, 0
    out, n = pat.subn(lambda m: m.group(1) + m.group(2) + m.group(4), text)
    return out, n


for rel in FILES:
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        problems.append('%s: not found' % rel)
        continue
    src = read(path)
    text = src
    notes = []

    # --- 1. the icons -----------------------------------------------------
    text, n_icons = strip_label_icons(rel, text)
    if n_icons:
        notes.append('%d label icon(s)' % n_icons)

    # --- 2. the move ------------------------------------------------------
    if rel in MOVES:
        mk = markup_only(text)
        src_span, why1 = row_span(mk, 'task_description')
        dst_span, why2 = row_before(mk, 'task_start_date')
        if src_span is None or dst_span is None:
            problems.append('%s: the move cannot be anchored - %s'
                            % (rel, why1 or why2))
        elif src_span[0] < dst_span[0]:
            notes.append('the description row is already above Schedule')
        else:
            a, b = src_span
            block = text[a:b]
            opens = len(re.findall(r'<div\b', block))
            # THE BLOCK MUST BE WHOLE, and this is the check the div
            # balance cannot be. A move that cuts a block short leaves the
            # missing tags behind, so the file still balances and still
            # renders wrong.
            if opens != block.count('</div>'):
                problems.append('%s: the row to move is not a whole block - '
                                '%d <div> and %d </div> in it'
                                % (rel, opens, block.count('</div>')))
            elif not block.lstrip().startswith('<div class="row">'):
                problems.append('%s: the block to move does not start with '
                                'the row - %r' % (rel, block[:40]))
            else:
                cut = text[:a] + text[b:]
                at = dst_span[0]
                text = cut[:at] + block + cut[at:]
                notes.append('task_description moved up (%d bytes, %d div(s),'
                             ' whole)' % (len(block), opens))

    # --- 3. the titles ----------------------------------------------------
    placed = []
    have = {h.strip() for h in re.findall(
        r'<%s class="%s"><i[^>]*></i>\s*([^<]+)</%s>' % (TAG, CLS, TAG),
        markup_only(text))}
    # PLACED LAST FIRST, so an insertion never moves the anchor of one
    # that has not been placed yet.
    for icon, title, kind, target in reversed(SECTIONS.get(rel, [])):
        if title.replace('&amp;', '&') in {h.replace('&amp;', '&')
                                           for h in have}:
            continue
        mk = markup_only(text)
        if kind == 'row':
            span, why = row_before(mk, target)
        elif kind == 'in_if':
            span, why = if_block_holding(mk, IF_COND, target)
        else:
            hits = [m for m in re.finditer(re.escape(target), mk)]
            if len(hits) != 1:
                span, why = None, ('%r appears %d time(s)'
                                   % (target, len(hits)))
            else:
                ls = mk.rfind('\n', 0, hits[0].start()) + 1
                span, why = (ls, hits[0].end()), None
        if span is None:
            problems.append('%s: %s - %s' % (rel, title, why))
            continue
        a, b = span
        if kind == 'in_if':
            at, pad = b, indent_at(text, a) + '  '
            if not text[at - 1:at] == '\n':
                at = text.find('\n', at) + 1
        else:
            at, pad = a, indent_at(text, a)
        text = text[:at] + heading(icon, title, pad) + text[at:]
        placed.append(title.replace('&amp;', '&'))
    placed.reverse()
    if placed:
        notes.append('%d title(s): %s' % (len(placed), ', '.join(placed)))

    if text == src:
        report.append('%-40s already done' % rel)
        continue
    planned[rel] = (path, src, text)
    report.append('%-40s %s' % (rel, '; '.join(notes)))


# ==========================================================================
# SELF-CHECK
# ==========================================================================
for rel, (path, src, text) in sorted(planned.items()):
    for tag in ('div', 'form', 'label', 'strong'):
        d0 = len(re.findall(r'<%s\b' % tag, src)) - src.count('</%s>' % tag)
        d1 = len(re.findall(r'<%s\b' % tag, text)) - text.count('</%s>' % tag)
        if d1 != d0:
            problems.append('%s: <%s> balance moved %d -> %d'
                            % (rel, tag, d0, d1))
    for tag in ('<form', '</form>'):
        if text.count(tag) < src.count(tag):
            problems.append('%s: %s count fell %d -> %d'
                            % (rel, tag, src.count(tag), text.count(tag)))

    # A TITLE ON THE WRONG SIDE OF AN {% if %} WOULD SHOW UP HERE. Every
    # Django tag this round leaves alone must still be there, in the same
    # number - push 3 learned to count these rather than trust the diff.
    def tags(t):
        return sorted(re.findall(r'\{%\s*(\w+)', t))
    if tags(src) != tags(text):
        problems.append('%s: the Django tags changed' % rel)

    # A FIELD STAYS IN ITS ROW. This is the invariant the div balance is
    # blind to. Grouping each row's fields and comparing the SET of groups
    # survives a whole row being moved - which is what this round does -
    # and fails the moment a row is cut short and its fields land in a
    # neighbour, which is what the first draft did while balancing
    # perfectly.
    def row_groups(t):
        mk = markup_only(t)
        out = []
        for m in ROW_OPEN.finditer(mk):
            end = close_of(mk, m.end())
            if end is None:
                out.append(('UNCLOSED',))
                continue
            out.append(tuple(re.findall(
                r'<(?:input|select|textarea)\b[^>]*\bname="([^"]+)"',
                mk[m.end():end])))
        return sorted(out)
    ga, gb = row_groups(src), row_groups(text)
    if ga != gb:
        only_a = [g for g in ga if g not in gb]
        only_b = [g for g in gb if g not in ga]
        problems.append('%s: a row\'s membership changed - was %s, is %s'
                        % (rel, only_a[:2], only_b[:2]))

    a, b = fields(src), fields(text)
    if sorted(a) != sorted(b):
        problems.append('%s: the SET of controls changed - %d before, %d '
                        'after' % (rel, len(a), len(b)))
        continue
    allowed = set(MOVES.get(rel, []))
    ra = [x for x in a if x not in allowed]
    rb = [x for x in b if x not in allowed]
    if ra != rb:
        i = next((k for k, (x, y) in enumerate(zip(ra, rb)) if x != y),
                 min(len(ra), len(rb)))
        problems.append('%s: fields this round did not name changed order - '
                        'at %d, %r became %r'
                        % (rel, i, ra[i:i + 1], rb[i:i + 1]))
    for x in sorted(allowed):
        if a.index(x) == b.index(x):
            problems.append('%s: %r is named as moving and did not move'
                            % (rel, x))

    # THE LABEL TEXT IS UNTOUCHED. Only the <i> is gone.
    def label_text(t):
        return [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', l)).strip()
                for l in re.findall(r'<label\b[^>]*>.*?</label>',
                                    markup_only(t), re.S)]
    # SORTED, because a round that moves a row moves its label with it.
    # Comparing the ordered list flagged project_subtasks_add for the one
    # move the round names, which is a check disagreeing with the plan
    # rather than finding a fault.
    if sorted(label_text(src)) != sorted(label_text(text)):
        problems.append('%s: a label\'s TEXT changed, not just its icon'
                        % rel)
    if re.search(r'<label\b[^>]*>\s*<i\s', markup_only(text)):
        problems.append('%s: a label still opens with an icon' % rel)

    # THE ONE TITLE THAT MUST BE INSIDE A CONDITIONAL, asserted by walking
    # the {% if %} stack rather than by trusting where it was inserted.
    for title, cond in INSIDE_IF.get(rel, []):
        mk = markup_only(text)
        pos = mk.find('%s</%s>' % (title, TAG))
        if pos < 0:
            problems.append('%s: %r is not in the file' % (rel, title))
            continue
        stack = []
        for m in re.finditer(r'\{%\s*(if|endif)\b[^%]*%\}', mk[:pos]):
            if m.group(1) == 'if':
                stack.append(re.sub(r'\s+', ' ', m.group(0)))
            elif stack:
                stack.pop()
        if cond not in stack:
            problems.append('%s: %r is not inside %s - open blocks are %s'
                            % (rel, title, cond, stack or 'none'))
    # and every OTHER title must be inside no conditional at all
    for m in re.finditer(r'<%s class="%s"><i[^>]*></i>\s*([^<]+)</%s>'
                         % (TAG, CLS, TAG), markup_only(text)):
        title = m.group(1).strip()
        if any(title == t for t, _c in INSIDE_IF.get(rel, [])):
            continue
        depth = 0
        for k in re.finditer(r'\{%\s*(if|endif)\b[^%]*%\}',
                             markup_only(text)[:m.start()]):
            depth += 1 if k.group(1) == 'if' else -1
        if depth != 0:
            problems.append('%s: %r sits %d conditional(s) deep and should '
                            'sit in none' % (rel, title, depth))


# ==========================================================================
print('\n' + '=' * 74)
print('ENTRY SECTIONS, PUSH 4 - THE PROJECTS SCREENS - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print("""
  No panel is built and no row is rebuilt: each screen is already one
  .form-card, so a section here is a title, as it is inside a modal body.
  No title goes inside a tab pane - the tab bar is the divider. Exactly one
  title goes inside a conditional, and the self-check walks the {% if %}
  stack to prove it rather than trusting where it was put.
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

for path, src, text in planned.values():
    bak = path + SUFFIX
    if not os.path.exists(bak):
        write(bak, src)
    write(path, text)

print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('  %d of them keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned.values() if CRLF.get(p[0])),
         sum(1 for p in planned.values() if not CRLF.get(p[0]))))
print('')
print('  Next:  python %s' % SUITE)
print('         python %s   (the gate)' % PS1)
