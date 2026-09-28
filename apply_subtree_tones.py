# -*- coding: utf-8 -*-
"""SECTION H, ROUND H7b - THE HEXES H7'S GLOB NEVER SAW

H7 pointed Bootstrap's SUCCESS and WARNING families at --alv-good and
--alv-warn, in base, so every page gets them without a rule of its own.
Its census ran over `glob('pages/templates/*.html')` and reported 114
uses across 35 files.

THAT GLOB DOES NOT DESCEND. pages/templates holds 138 templates, and
eighteen of them live in six subdirectories - projects/ alone has eleven.
H7 saw 120. It was test_hub_bar.py, during H8's sweep, that said so: its
own census walks the tree, and it named three projects/ pages H7 had
never looked at.

H7'S OUTCOME WAS NOT WRONG, ONLY ITS ARITHMETIC. The fix lives in base,
which every one of those eighteen templates extends, so the fifteen
success and warning uses in the subtree were already corrected the day
H7 deployed. What H7 could not do, because it never saw them, is delete
the page-level rules that OVERRIDE base in that subtree. Four hexes and
one keyword, in three files:

    projects/project_tasks_delete   .subtasks-warning .text-warning
                                      color: #856404 !important
    projects/project_tasks_edit     .text-warning  color: #856404
                                    .alert-success border-color: #28a745
                                    .alert-warning border-color: #ffc107
    projects/projects_detail        .btn-warning   #0e7c8b and `white`
                                    .btn-warning:hover

THIS IS NOT A CONTRAST ROUND, AND SAYING SO IS THE POINT.
    #856404 measures 5.49 on white; --alv-warn #8e6207 measures 5.38. The
    house token is a HAIR WORSE and both pass AA comfortably. What this
    round buys is that the system has ONE amber instead of two, and that
    four hexes leave a page's own style block - which 3.1 forbids in as
    many words, because a hex is invisible to a token audit.

    The alert EDGES do change visibly. Bootstrap's #28a745 rim measures
    2.76 against the tint inside it; the house --alv-good-line is 1.25,
    which is where H7 deliberately put it to match the accent family's
    1.36. Those two alerts will read quieter. That is the house look, and
    it is the only thing on this round anyone will see.

TWO OF THE FIVE ARE DEAD, AND WERE ALREADY
    .btn-warning on projects_detail has NO WEARER - not in the markup,
    not in a script. Somebody retoned a Bootstrap warning button to the
    accent by hand, in a hex, and then the button went away. Its :hover
    twin is the only rule in its @media block, so the block goes too.
    .text-warning on project_tasks_edit has no wearer either.

    The two alert rules there DO have wearers, built inside a script -
    which is exactly why base owning the family matters: the class is the
    same whether a template typed it or JavaScript injected it.

ONE RULE IS EDITED, NOT DELETED
    .subtasks-warning .text-warning also carries font-weight and
    margin-bottom. Those are layout, this page's own business, and they
    stay. Only the colour goes.

WHAT IS LEFT ALONE, AND WHY
    manual_pdf.html keeps its five - a PRINT document, flat on purpose,
    already recorded by H7.
    personal_notification_settings keeps .notification-card .btn-success,
    which sets a width and a padding and no colour at all. It is a
    button, and buttons are the retone round's, per 3.1a.

Backups: .bak_subtree. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_subtree'
CRLF = {}


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
            raise SystemExit('H7b: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70. All three files here are LF today; the helper stays
    because that is a fact about today, not about the repo."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def cut(path, text, block, why):
    """Remove `block` exactly once, taking its line's indent and the
    newline after it.

    THE TAIL TRIM CONSUMES \\r as well as spaces and tabs - H7 found that
    the hard way on a CRLF file, where stopping at the '\\r' leaves it
    behind as a blank line."""
    b = eol(path, block)
    n = text.count(b)
    if n != 1:
        raise SystemExit('H7b: %s - %s is there %d time(s), not 1'
                         % (os.path.basename(path), why, n))
    s = text.index(b)
    head = text.rfind('\n', 0, s) + 1
    if text[head:s].strip():
        head = s
    e = s + len(b)
    while e < len(text) and text[e] in ' \t\r':
        e += 1
    if e < len(text) and text[e] == '\n':
        e += 1
    # A RULE SITTING BETWEEN TWO BLANK LINES LEAVES TWO BEHIND. Taking
    # the block and the blank line after it still leaves the one before,
    # next to the one that followed the NEXT thing - so two deletions in
    # a row opened a three-line gap in projects_detail. Give the block
    # one of its two surrounding blanks.
    tail = text[e:].replace('\r\n', '\n')
    if text[:head].replace('\r\n', '\n').endswith('\n\n') \
            and tail.startswith('\n'):
        head = text.rfind('\n', 0, head - 1) + 1
    return text[:head] + text[e:]


# ==========================================================================
# (relative path, [(what it is, the exact block)], [(edit: was, now)])
#
# Exact blocks, not patterns. Five rules in three files does not need a
# rule parser, and an exact block that stops matching is a louder failure
# than a pattern that silently matches something else.
DROPS = [
    ('projects/projects_detail.html', [
        ('the dead .btn-warning',
         '.btn-warning {\n'
         '    background-color: #0e7c8b;\n'
         '    border-color: #0e7c8b;\n'
         '    color: white;\n'
         '    transition: all 0.3s ease;\n'
         '    border-radius: 6px;\n'
         '    font-weight: 500;\n'
         '}'),
        ('its :hover, and the @media block that holds nothing else',
         '@media (hover: hover) and (pointer: fine) {\n'
         '    .btn-warning:hover {\n'
         '        background-color: var(--alv-accent-ink);\n'
         '        border-color: var(--alv-accent-ink);\n'
         '        color: white;\n'
         '        transform: translateY(-1px);\n'
         '        box-shadow: 0 2px 4px rgba(0,0,0,0.2);\n'
         '    }\n'
         '}'),
    ]),
    ('projects/project_tasks_edit.html', [
        ('the dead .text-warning',
         '.text-warning { color: #856404 !important; font-weight: 600; }'),
        ("a Bootstrap green edge base now draws in --alv-good-line",
         '.alert-success { border-color: #28a745; }'),
        ("a Bootstrap amber edge base now draws in --alv-warn-line",
         '.alert-warning { border-color: #ffc107; }'),
    ]),
]

# The one rule that is edited rather than deleted: its colour goes, its
# layout stays.
EDITS = [
    ('projects/project_tasks_delete.html',
     'the colour only - font-weight and margin-bottom are this page\'s',
     '.subtasks-warning .text-warning {\n'
     '    color: #856404 !important;\n'
     '    font-weight: 600;\n'
     '    margin-bottom: 8px;\n'
     '}',
     '.subtasks-warning .text-warning {\n'
     '    font-weight: 600;\n'
     '    margin-bottom: 8px;\n'
     '}'),
]

# Named, so that a page joining this list later is a decision somebody
# made rather than a glob that moved.
LEAVE = {
    'manual_pdf.html':
        'a PRINT document, flat on purpose - recorded by H7',
    'personal_notification_settings.html':
        'a width and a padding, no colour - a button, so 3.1a',
}

# Every hex this round is removing, so the suite can prove they are gone
# and that none of them came back.
HEXES = ['#856404', '#28a745', '#ffc107', '#0e7c8b']

# ==========================================================================
print('=' * 74)
print('SECTION H, ROUND H7b - THE HEXES H7\'S GLOB NEVER SAW%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed = already = 0

for rel, blocks in DROPS:
    path = os.path.join(ROOT, *rel.split('/'))
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)
    before = text
    todo = [(why, b) for why, b in blocks if eol(path, b) in text]
    if not todo:
        print('  %-38s already given up' % rel)
        already += 1
        continue
    for why, b in todo:
        text = cut(path, text, b, why)
        print('  %-38s - %s' % (rel, why))
    # NOTHING ELSE MOVED. Each block is removed with its own line's
    # indent and the newline after it, so the file must shrink by the
    # blocks' own length plus at most one line-ending each - never more.
    lost = len(before) - len(text)
    least = sum(len(eol(path, b)) for _, b in todo)
    if not least <= lost <= least + 8 * len(todo):
        raise SystemExit('H7b: %s lost %d characters for %d of block - '
                         'something outside the blocks moved'
                         % (rel, lost, least))
    changed += 1
    if not CHECK:
        back_up(path, raw)
        write(path, text)

for rel, why, was, nowtext in EDITS:
    path = os.path.join(ROOT, *rel.split('/'))
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)
    a, b = eol(path, was), eol(path, nowtext)
    if a not in text:
        print('  %-38s already given up' % rel)
        already += 1
        continue
    if text.count(a) != 1:
        raise SystemExit('H7b: %s - the rule is there %d time(s), not 1'
                         % (rel, text.count(a)))
    text = text.replace(a, b, 1)
    print('  %-38s ~ %s' % (rel, why))
    changed += 1
    if not CHECK:
        back_up(path, raw)
        write(path, text)

for rel, why in sorted(LEAVE.items()):
    print('  %-38s -  %s' % (rel, why))

print('-' * 74)
print('  %d changed, %d already in place' % (changed, already))
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
