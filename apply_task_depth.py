# -*- coding: utf-8 -*-
"""PJ-6 - THE TASK TREE ON A PHONE, AND THE COLOUR THAT WAS BEING THROWN AWAY

Demetri chose "indent + depth-shaded bar" for the Task List phone cards.
Measuring first changed the round.

==========================================================================
THE DEPTH CUE IS NOT WEAK ON A PHONE. IT IS GONE.
==========================================================================
On a desktop each row carries a 4px coloured left border and a faint tint
by type - blue project, green task, amber subtask. Rendered at 390px, all
three cards come out:

    width        366px   366px   366px
    left edge     12px    12px    12px
    left border  1px grey 1px grey 1px grey
    background   white   white   white

IDENTICAL. base's card rule sets `border: 1px solid var(--alv-line)` and
`background: var(--alv-paper)` - both shorthands, both later in the
cascade - so the page's coloured bar and its tint are discarded. All that
distinguishes a subtask from a project is the NAME shifting 12px, because
the indent is on a div INSIDE the cell rather than on the card.

So the page already had the language. It stopped working at 768px.

==========================================================================
WHAT THIS ROUND DOES
==========================================================================
1. THE CARD INDENTS, NOT THE NAME. 14px per level, keyed on a new
   task-depth-N class on the row - depth is the fact, and the type class
   only happens to agree with it today. At subtask depth the card is 338px
   of 366, and the step is visible because the card's EDGE moves.

2. THE COLOURED BAR COMES BACK on the phone card, so depth reads the same
   way on both screens.

3. AND THE THREE COLOURS BECOME THE HOUSE CATEGORY FAMILY. base lifted
   --alv-tag-sky-ink, -moss-ink and -clay-ink out of the chip rules on
   29 Sep for exactly this - "so that something which is not a chip can
   use one". They are muted where Bootstrap's #3498db, #2ecc71 and
   #f39c12 are bright, so this IS a visible change on the desktop too,
   and it is the point: a type is a CATEGORY, and the house has a
   categorical palette.

4. THE PROJECT ROW LOSES ITS TWO DEAD ICONS. Demetri's call. They are
   titled "Not available here" and can never be pressed on any project.
   GATED ON task_obj, NOT ON PERMISSION: the same else-branch is what a
   READ-ONLY user sees on every task and subtask, and removing it
   wholesale would have taken the disabled state away from them too.

22 hex uses across 10 colours go onto tokens. The print black stays: a
printed border should be black, and no token says black.

Backups: .bak_taskdepth. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_taskdepth'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

PAGE = None
for p in alv_tree.templates():
    if alv_tree.rel(p).replace(os.sep, '/') == 'projects/project_task_list.html':
        PAGE = p
if PAGE is None:
    raise SystemExit('PJ6: projects/project_task_list.html is not in the tree')

# Ordinary ink and line. Straightforward.
TOKENS = [
    ('#dee2e6', 'var(--alv-line)'),
    ('#2c3e50', 'var(--alv-ink)'),
    ('#495057', 'var(--alv-ink-soft)'),
    ('#6c757d', 'var(--alv-ink-soft)'),
    ('#0e7c8b', 'var(--alv-accent)'),
    ('#e74c3c', 'var(--alv-bad)'),
    # THE CATEGORY FAMILY. Not --alv-good and --alv-warn: those are
    # SEMANTIC, and a subtask is not a warning. base keeps the two sets
    # apart on purpose and says so where it declares them.
    ('#3498db', 'var(--alv-tag-sky-ink)'),
    ('#2ecc71', 'var(--alv-tag-moss-ink)'),
    ('#f39c12', 'var(--alv-tag-clay-ink)'),
]


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('PJ6: %s is not a byte copy' % bak)


def swap(nl, old, new, what, times=1):
    c = nl.count(old)
    if c != times:
        raise SystemExit('PJ6: %s appears %d times, not %d'
                         % (what, c, times))
    return nl.replace(old, new)


def outside_comments(text, fn):
    """Apply FN to the parts of TEXT that are not a Django comment.

    A note recording what a colour USED to be must keep saying it. The
    page carries one: a comment about a label that had drifted to
    '11px UPPERCASE #6c757d'. Rewriting that to name a token would make
    the record of a past wrong into a description of a present right.
    Same lesson CO-1 spent a round on, from the other side.
    """
    out, i = [], 0
    for m in re.finditer(r'\{#.*?#\}', text, re.S):
        out.append(fn(text[i:m.start()]))
        out.append(m.group(0))
        i = m.end()
    out.append(fn(text[i:]))
    return ''.join(out)


print('=' * 74)
print('PJ-6 - THE TASK TREE ON A PHONE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')

if 'PJ-6, 4 Oct 2026' in nl:
    print('  project_task_list.html     already converted')
else:
    # ---- 1. THE ROW CARRIES ITS DEPTH ---------------------------------
    nl = swap(nl, '<tr class="task-row task-type-{{ item.type|lower }}">',
              '{# PJ-6, 4 Oct 2026 - THE ROW CARRIES ITS DEPTH. The type   #}\n'
              '          {# class happens to agree with it today, but depth is  #}\n'
              '          {# the fact the indent is about, and a fourth level     #}\n'
              '          {# would need no new class here.                       #}\n'
              '          <tr class="task-row task-type-{{ item.type|lower }} '
              'task-depth-{{ item.indent_level }}">',
              'the row tag')

    # ---- 2. THE PROJECT ROW LOSES ITS DEAD ICONS ----------------------
    # GATED ON task_obj. The else-branches below are ALSO what a read-only
    # user sees on a real task, so they stay - what goes is the whole cell
    # on a row that has no task behind it at all.
    nl = swap(nl, '            <td class="desktop-action-cell cell-actions">\n'
                  '              <span class="row-actions">\n',
              '            {# PJ-6 - A PROJECT ROW HAS NO TASK BEHIND IT, so it  #}\n'
              '            {# gets no actions rather than two greyed ones titled #}\n'
              '            {# "Not available here". The cell stays so the column #}\n'
              '            {# still lines up; what goes is its contents.         #}\n'
              '            {# ON task_obj, NOT ON PERMISSION - the disabled pair  #}\n'
              '            {# below is what a READ-ONLY user sees on a real task. #}\n'
              '            <td class="desktop-action-cell cell-actions">\n'
              '              {% if item.task_obj %}\n'
              '              <span class="row-actions">\n',
              'the desktop actions cell')
    nl = swap(nl, '              </span>\n'
                  '            </td>\n\n'
                  '            <td class="mobile-action-bar cols-2">\n',
              '              </span>\n'
              '              {% endif %}\n'
              '            </td>\n\n'
              '            {% if item.task_obj %}\n'
              '            <td class="mobile-action-bar cols-2">\n',
              'the end of the desktop cell')
    # ANCHORED ON THE ROW ABOVE IT, not on the closing tags alone: the
    # empty-state row two lines below ends in exactly the same three lines,
    # and a slice taken from the wrong one would have gated the "no tasks
    # found" message on a task existing.
    nl = swap(nl, '                </span>\n'
                  '              {% endif %}\n'
                  '            </td>\n'
                  '          </tr>\n',
              '                </span>\n'
              '              {% endif %}\n'
              '            </td>\n'
              '            {% endif %}\n'
              '          </tr>\n',
              'the end of the mobile cell')

    # ---- 3. THE PHONE RULES -------------------------------------------
    OLD_PH = """    .task-indent-0 { padding-left: 0; }
    .task-indent-1 { padding-left: 12px; }
    .task-indent-2 { padding-left: 24px; }
"""
    NEW_PH = """    /* PJ-6, 4 Oct 2026 - THE CARD INDENTS, NOT THE NAME.
       These three shifted the name inside the cell by 12 and 24px, which
       on a card reads as a wobble rather than a tree: every card was the
       same 366px wide and started at the same edge. The CARD steps now,
       so the hierarchy is in the shape of the list.

       base sets width:100% on the row, so the width is taken back by the
       same amount - otherwise each level would hang off the right. */
    .task-indent-0,
    .task-indent-1,
    .task-indent-2 { padding-left: 0; }

    .alv-table tbody tr.task-depth-1 {
        margin-left: 14px;
        width: calc(100% - 14px);
    }
    .alv-table tbody tr.task-depth-2 {
        margin-left: 28px;
        width: calc(100% - 28px);
    }

    /* AND THE COLOURED BAR COMES BACK.
       base's card rule writes `border: 1px solid var(--alv-line)` - a
       SHORTHAND, later in the cascade - so the 4px type border the
       desktop shows was being thrown away here, along with the tint.
       Restated at (0,2,2) against base's (0,1,2), so it wins on weight
       and not on order. */
    .alv-table tbody tr.task-type-project {
        border-left: 4px solid var(--alv-tag-sky-ink);
    }
    .alv-table tbody tr.task-type-task {
        border-left: 4px solid var(--alv-tag-moss-ink);
    }
    .alv-table tbody tr.task-type-subtask {
        border-left: 4px solid var(--alv-tag-clay-ink);
    }
"""
    nl = swap(nl, OLD_PH, NEW_PH, 'the phone indent rules')

    # ---- 4. AND THE HEXES GO ------------------------------------------
    def retone(chunk):
        for hexv, token in TOKENS:
            chunk = re.sub(re.escape(hexv) + r'\b', token, chunk, flags=re.I)
        return chunk

    before = sum(len(re.findall(re.escape(h) + r'\b', nl, re.I))
                 for h, _ in TOKENS)
    nl = outside_comments(nl, retone)

    out = nl.replace('\n', '\r\n') if CRLF.get(PAGE) else nl
    if not CHECK:
        back_up(PAGE, raw)
        write(PAGE, out)
    print('  project_task_list.html     depth on the row, the bar restored, '
          '%d hex use(s) on tokens' % before)

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
src = alv_tree.code_only(read(PAGE)[0])
old = alv_tree.code_only(read(PAGE + SUFFIX)[0])
raw_now = read(PAGE)[0]

# 1. THE ROW CARRIES ITS DEPTH, AND THE TEMPLATE STILL HAS THE VALUE.
if 'task-depth-{{ item.indent_level }}' not in src:
    raise SystemExit('PJ6: the row does not carry its depth')
if 'task-depth' in old:
    raise SystemExit('PJ6: CONTROL FAILED - the backup already had it')
print('  the row carries task-depth-N, from indent_level')

# 2. THE INDENT IS ON THE ROW AND NO LONGER ON THE NAME.
css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
phone = css[css.index('@media screen and (max-width: 768px)'):]
for lvl, px in ((1, 14), (2, 28)):
    r = re.search(r'\.alv-table tbody tr\.task-depth-%d\s*\{([^}]*)\}' % lvl,
                  phone)
    if not r:
        raise SystemExit('PJ6: no phone rule for depth %d' % lvl)
    if 'margin-left: %dpx' % px not in r.group(1):
        raise SystemExit('PJ6: depth %d is not %dpx' % (lvl, px))
    if 'calc(100%% - %dpx)' % px not in r.group(1):
        raise SystemExit('PJ6: depth %d does not take the width back, so '
                         'the card would hang off the right' % lvl)
print('  the card steps 14px a level, and gives the width back')

if not re.search(r'\.task-indent-0,\s*\.task-indent-1,\s*\.task-indent-2\s*'
                 r'\{\s*padding-left: 0;\s*\}', phone):
    raise SystemExit('PJ6: the name still indents on a phone - two things '
                     'would be saying one')
print('  and the name inside it does not, so one thing says it')

# 3. THE BAR IS BACK, AND BEATS base ON WEIGHT.
for kind, token in (('project', 'sky'), ('task', 'moss'),
                    ('subtask', 'clay')):
    r = re.search(r'\.alv-table tbody tr\.task-type-%s\s*\{([^}]*)\}' % kind,
                  phone)
    if not r or 'var(--alv-tag-%s-ink)' % token not in r.group(1):
        raise SystemExit('PJ6: the %s bar is not restored on the phone card'
                         % kind)
print('  all three bars are restored on the phone card')

obar = re.search(r'@media screen and \(max-width: 768px\)', old)
if obar and 'task-type-project' in old[obar.start():]:
    raise SystemExit('PJ6: CONTROL FAILED - the backup already restored it')
print('  CONTROL: the backup restored none of them')

# 4. THE PROJECT ROW HAS NO ACTIONS, AND A READ-ONLY USER STILL DOES.
i = src.index('<td class="desktop-action-cell cell-actions">')
j = src.index('</tr>', i)
cell = src[i:j]
if '{% if item.task_obj %}' not in cell:
    raise SystemExit('PJ6: the actions are not gated on task_obj')
if 'icon-disabled' not in cell:
    raise SystemExit('PJ6: the disabled pair is gone entirely - that is '
                     'what a READ-ONLY user sees on a real task')
if 'perms.auth.can_edit_projects' not in cell:
    raise SystemExit('PJ6: the permission branch is gone')
if cell.count('<td class="mobile-action-bar') != 1:
    raise SystemExit('PJ6: the mobile bar is not where it was')
if src.count('{% if item.task_obj %}') != 2:
    raise SystemExit('PJ6: expected both cells gated, found %d gate(s)'
                     % src.count('{% if item.task_obj %}'))
print('  a project row renders no actions; a read-only user keeps the '
      'disabled pair on a real task')

# 5. THE HEXES.
left = [h for h in re.findall(r'#[0-9a-fA-F]{3,6}\b',
                              re.sub(r'\{#.*?#\}', '', src, flags=re.S))]
if left != ['#000']:
    raise SystemExit('PJ6: hex(es) left outside the print rule: %s' % left)
print('  the only hex left is the print black, and a printed border '
      'should be black')

for hexv, token in TOKENS:
    n = len(re.findall(re.escape(hexv) + r'\b', old, re.I))
    if not n:
        raise SystemExit('PJ6: CONTROL FAILED - %s was not in the backup'
                         % hexv)
    if token not in src:
        raise SystemExit('PJ6: %s is not on the page' % token)
print('  and all %d of them resolve to a token' % len(TOKENS))

# 6. A NOTE THAT RECORDS AN OLD COLOUR STILL RECORDS IT.
if '#6c757d' not in raw_now:
    raise SystemExit('PJ6: the note about a label that had drifted to '
                     '#6c757d was rewritten - a record of a past wrong is '
                     'not a description of a present right')
print('  CONTROL: the note recording a drifted colour still names it')

print('-' * 74)
print('  The page already had the language. It stopped working at 768px,')
print('  because a shorthand later in the cascade threw the bar away.')
print('=' * 74)
