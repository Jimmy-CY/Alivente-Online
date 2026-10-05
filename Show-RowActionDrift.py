# -*- coding: utf-8 -*-
"""Show-RowActionDrift.py - which action columns have left the house order.

RA-1, 4 Oct 2026. Demetri: "We should define a standard order that we
place all icons in all tables, in the Action Column and apply this across
the app."

    LOOK -> CHANGE -> COPY -> ADVANCE -> DESTROY

The order lives in alv_rowactions.py and nowhere else; this report and
test_row_action_order.py both ask it, so there is one rule rather than
three copies of one.

    python Show-RowActionDrift.py            every wrapper, with its order
    python Show-RowActionDrift.py --strict   exit 1 if anything has drifted
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
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import alv_tree
import alv_rowactions as RA

STRICT = '--strict' in sys.argv
QUIET = '--quiet' in sys.argv


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def line(s=''):
    print(s)


line('=' * 74)
line(' ROW ACTION DRIFT - action columns that have left the house order')
line('=' * 74)
line()
line('   LOOK -> CHANGE -> COPY -> ADVANCE -> DESTROY')
line('   within LOOK: the record, then its papers, then its children')
line()

rows = []
glyphs = {}
# RA-2, 5 Oct 2026 - what is NOT in a wrapper.
#
# This report has always read the tree through RA.wrappers(), which finds
# .row-actions on a <span> or a <div>. 83 icon buttons are inside one;
# THIRTY-SEVEN ARE NOT, across fourteen pages, and the report said nothing
# about them at all.
#
# A report silent about a third of its subject is worse than no report,
# because it is believed. Inside this blind spot .icon-view carried four
# pictures, .icon-approve drew an undo arrow, and four passport buttons
# had no verb in their markup.
#
# They are NAMED here rather than failed on: wrapping all 37 is ~21 edits
# over fourteen pages, ten inside <td> elements where .row-actions'
# inline-flex would break the cell. That is RA-3.
loose = {}
for p in sorted(alv_tree.templates()):
    name = alv_tree.rel(p).replace(os.sep, '/')
    src = alv_tree.code_only(read(p))
    for names, gl in RA.unwrapped(src):
        loose.setdefault(name, []).append((names, gl))
        # AND THE GLYPH CENSUS COUNTS THEM NOW. This is exactly where
        # .icon-view hid four pictures: the census only ever looked
        # inside wrappers, so three strays were never compared against
        # the eleven that were right.
        for c in names:
            if c != 'icon-disabled' and gl:
                glyphs.setdefault(c, set()).add(gl[0])

    for s, e, inner in RA.wrappers(src):
        seq = RA.sequence(inner)
        if seq:
            rows.append((name, seq, RA.unfixable(inner)))
        for m in re.finditer(
                r'class="([^"]*icon-action-btn[^"]*)"[^>]*>\s*'
                r'<i class="[^"]*?(fa-[a-z0-9-]+)', inner, re.S):
            for c in m.group(1).split():
                if c.startswith('icon-') and c not in ('icon-action-btn',
                                                       'icon-disabled'):
                    glyphs.setdefault(c, set()).add(m.group(2))
                    break

drift = [(n, s) for n, s, _ in rows if len(s) >= 2 and not RA.in_order(s)]
stuck = [(n, u) for n, _, u in rows if u]
twopic = {c: g for c, g in glyphs.items() if len(g) > 1}

if not QUIET:
    for name, seq, _ in rows:
        mark = ''
        if len(seq) >= 2 and not RA.in_order(seq):
            mark = '   <-- OUT OF ORDER'
        line('   %-42s %s%s' % (name, ' -> '.join(seq), mark))
    line()

line('   %d wrapper(s) on %d page(s); %d with two or more actions'
     % (len(rows), len({n for n, _, _ in rows}),
        len([1 for _, s, _ in rows if len(s) >= 2])))
line()

problems = 0

if drift:
    problems += len(drift)
    line('   OUT OF ORDER')
    for name, seq in drift:
        want = sorted(seq, key=lambda v: (RA.FAMILY[v], RA.WITHIN.get(v, 0)))
        line('     %-40s %s' % (name, ' -> '.join(seq)))
        line('     %-40s %s' % ('   should read', ' -> '.join(want)))
    line()
else:
    line('   Every action column is in house order.')
    line()

if stuck:
    problems += len(stuck)
    line('   OUT OF ORDER INSIDE ONE BLOCK - sorting cannot repair these,')
    line('   because the two controls share a permission test. By hand.')
    for name, u in stuck:
        for seq in u:
            line('     %-40s %s' % (name, ' -> '.join(seq)))
    line()

# A CLASS CARRIES ONE PICTURE. base states this beside .icon-duplicate,
# .icon-manage and .icon-list; RA-1 found .icon-view carrying four, and
# the ORDER sorts on the name, so a class with two pictures is two
# different actions that cannot be told apart or placed.
if twopic:
    problems += len(twopic)
    line('   MORE THAN ONE PICTURE ON ONE NAME')
    for c, g in sorted(twopic.items()):
        line('     %-40s %s' % (c, ', '.join(sorted(g))))
    line()
else:
    line('   Every icon class carries exactly one picture.')
    line()

# NOT COUNTED AS DRIFT, but worth seeing: two NAMES on one picture is the
# other direction, and it is pre-existing - icon-lock and icon-void both
# draw fa-ban. A reader cannot tell them apart either, but nothing in
# this round created it and guessing at a replacement glyph is a
# decision, not a repair.
byglyph = {}
for c, g in glyphs.items():
    for one in g:
        byglyph.setdefault(one, set()).add(c)
shared = {g: c for g, c in byglyph.items() if len(c) > 1}
if shared:
    line('   NOTED, NOT DRIFT - one picture worn by two names:')
    for g, cs in sorted(shared.items()):
        line('     %-40s %s' % (g, ', '.join(sorted(cs))))
    line()

# NOT COUNTED AS DRIFT - named so the blind spot is visible, not so the
# report fails on work nobody has agreed to do. RA-3 wraps them.
if loose:
    n = sum(len(v) for v in loose.values())
    line('   NOT IN A .row-actions WRAPPER - %d button(s) on %d page(s).'
         % (n, len(loose)))
    line('   The ordering standard cannot be read on these. Until RA-2')
    line('   the glyph census could not see them either.')
    for pg in sorted(loose):
        seen = sorted({' '.join(c) or '(no icon class)'
                       for c, _ in loose[pg]})
        line('     %-40s %2d  %s' % (pg, len(loose[pg]), ', '.join(seen)))
    line()

line('=' * 74)
if problems:
    line('   %d problem(s).' % problems)
else:
    line('   Nothing drifting.')
line('=' * 74)

sys.exit(1 if (STRICT and problems) else 0)
