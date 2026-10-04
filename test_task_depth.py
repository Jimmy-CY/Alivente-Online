# -*- coding: utf-8 -*-
"""test_task_depth.py - Section PJ round PJ-6, 4 Oct 2026.

Demetri chose "indent + depth-shaded bar" for the Task List phone cards.
Measuring first changed the round.

==========================================================================
THE DEPTH CUE WAS NOT WEAK ON A PHONE. IT WAS GONE.
==========================================================================
A desktop row carries a 4px coloured left border by type - blue project,
green task, amber subtask. At 390px all three cards measured IDENTICAL:
366px wide, same left edge, same white ground, same 1px grey border.

base's card rule writes `border: 1px solid var(--alv-line)` and
`background: var(--alv-paper)` - both SHORTHANDS, both later in the
cascade - so the page's coloured bar and its tint were thrown away. All
that separated a subtask from a project was the NAME shifting 12px,
because the indent sat on a div inside the cell rather than on the card.

SECTION 2 IS THE ROUND, and it is driven in a browser because the claim is
a cascade claim: the before and after are rendered at 390px and the card
EDGES are compared. 12 / 12 / 12 before; 12 / 26 / 40 after, with the
widths given back so nothing hangs off the right.

AND SECTION 3 IS THE SCOPE GUARD. The three colours become the house
CATEGORY family - --alv-tag-sky-ink, -moss-ink, -clay-ink, which base
lifted out of the chip rules on 29 Sep "so that something which is not a
chip can use one". They are muted where Bootstrap's were bright, so the
DESKTOP changes too. Section 3 renders it and fails if anything but the
bar colour moved.
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
import ast
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_taskdepth'
ME = 'test_task_depth.py'
PATCHER = 'apply_task_depth.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_taskdepth_')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code(p):
    return alv_tree.code_only(now(p))

import os
PAGE = [p for p in alv_tree.templates()
        if alv_tree.rel(p).replace(os.sep, '/')
        == 'projects/project_task_list.html'][0]
BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
SRC = alv_tree.code_only(now(PAGE))
OLD = alv_tree.code_only(was(PAGE)) if was(PAGE) else ''
RAW = now(PAGE)

TOKENS = [('#dee2e6', 'var(--alv-line)'), ('#2c3e50', 'var(--alv-ink)'),
          ('#495057', 'var(--alv-ink-soft)'), ('#6c757d', 'var(--alv-ink-soft)'),
          ('#0e7c8b', 'var(--alv-accent)'), ('#e74c3c', 'var(--alv-bad)'),
          ('#3498db', 'var(--alv-tag-sky-ink)'),
          ('#2ecc71', 'var(--alv-tag-moss-ink)'),
          ('#f39c12', 'var(--alv-tag-clay-ink)')]
KINDS = (('project', 'sky', 0), ('task', 'moss', 1), ('subtask', 'clay', 2))


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def phone_of(x):
    c = css_of(x)
    i = c.find('@media screen and (max-width: 768px)')
    return c[i:] if i >= 0 else ''


# ==========================================================================
head('1. THE ROW CARRIES ITS DEPTH, AND THE NAME STOPS PRETENDING TO')
# ==========================================================================
ok('task-depth-{{ item.indent_level }}' in SRC,
   'the row carries task-depth-N, built from indent_level')
ok(OLD and 'task-depth' not in OLD,
   'CONTROL: the backup had no depth on the row at all')
# DEPTH, NOT TYPE. They agree today - project 0, task 1, subtask 2 - but
# depth is the fact the indent is about, and a fourth level would need no
# new class.
# BY ITS PATH, NOT BY WALKING FOR IT. Third time: LZ-1 and BK-1 both
# shipped a suite that walked for a view file and landed on the debt
# register test_waiting_down keeps. os.walk over a root a file built for
# itself is what alv_tree exists to replace, and it finds the first file
# of that name anywhere - backups included.
_vp = os.path.join(ROOT, 'pages', 'views', 'projects.py')
v = read(_vp) if os.path.isfile(_vp) else ''
ok(v and "'indent_level': 0" in v and "'indent_level': 2" in v,
   'and the view really sets it, 0 through 2', bool(v))

PH = phone_of(SRC)
ok(bool(re.search(r'\.task-indent-0,\s*\.task-indent-1,\s*\.task-indent-2\s*'
                  r'\{\s*padding-left: 0;\s*\}', PH)),
   'the name no longer indents on a phone - two things would be saying one')
if OLD:
    ok('padding-left: 12px' in phone_of(OLD),
       'CONTROL: the backup shifted the name by 12px and 24px')

# ==========================================================================
head('2. THE CARDS, IN A BROWSER, AT 390px')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

ROWS = [('project', 0, 'Roof Replacement'),
        ('task', 1, 'Obtain three quotes'),
        ('subtask', 2, 'Chase the second quote')]


def cards(src, depth_class):
    """The page's cards at phone width, under base's stylesheet AND
    Bootstrap's reset - which is where box-sizing comes from. Without it
    a card measures 416px in a 390px viewport and the fixture reports an
    overflow the page does not have."""
    trs = ''.join(
        '<tr class="task-row task-type-%s%s">'
        '<td class="task-name-cell" data-label="Name">'
        '<div class="task-indent-%d"><i class="fas fa-folder-open"></i>'
        '<strong class="task-name">%s</strong></div></td>'
        '<td data-label="Type">%s</td>'
        '<td data-label="Status">In Progress</td></tr>'
        % (t, (' task-depth-%d' % d) if depth_class else '', d, n, t.title())
        for t, d, n in ROWS)
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style><style>%s</style></head>'
            '<body style="margin:0;padding:12px"><div class="table-container">'
            '<table class="table alv-table task-list-table"><tbody>%s</tbody>'
            '</table></div></body></html>'
            % (read(BOOT) if os.path.exists(BOOT) else '',
               css_of(alv_tree.code_only(now(BASE))), css_of(src), trs))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 390, 'height': 900})
        pg.set_content(html)
        pg.wait_for_timeout(150)
        r = pg.evaluate("""() => ({
          scroll: document.documentElement.scrollWidth,
          rows: [...document.querySelectorAll('tr.task-row')].map(tr => {
            const rr = tr.getBoundingClientRect();
            const s = getComputedStyle(tr);
            return {t: tr.className.match(/task-type-(\\w+)/)[1],
                    left: Math.round(rr.left),
                    w: Math.round(rr.width),
                    bw: s.borderLeftWidth,
                    bc: s.borderLeftColor};})})""")
        b.close()
    return r


if sync_playwright is None or not OLD:
    for _ in range(8):
        skip('the cards at 390px', 'playwright or backup missing')
else:
    A = cards(was(PAGE), False)
    B = cards(now(PAGE), True)

    ok(len(set(x['left'] for x in A['rows'])) == 1,
       'CONTROL: before this round all three cards began at the same edge, '
       '%dpx' % A['rows'][0]['left'])
    ok(len(set(x['w'] for x in A['rows'])) == 1,
       '  and were the same width, %dpx' % A['rows'][0]['w'])
    ok(len(set(x['bc'] for x in A['rows'])) == 1,
       '  and wore the same grey bar - the type colour was thrown away',
       set(x['bc'] for x in A['rows']))

    lefts = [x['left'] for x in B['rows']]
    ok(lefts[1] - lefts[0] == 14 and lefts[2] - lefts[1] == 14,
       'now each level steps 14px: %s' % lefts)
    widths = [x['w'] for x in B['rows']]
    ok(widths == [widths[0], widths[0] - 14, widths[0] - 28],
       '  and gives the width back, so nothing hangs off the right: %s'
       % widths)
    ok(B['scroll'] == 390,
       '  with no horizontal scroll at all - scrollWidth %d' % B['scroll'])
    ok(all(x['bw'] == '4px' for x in B['rows']),
       '  and the bar is 4px on every card')
    ok(len(set(x['bc'] for x in B['rows'])) == 3,
       '  in three different colours - %s'
       % ', '.join('%s %s' % (x['t'], x['bc']) for x in B['rows']))

# ==========================================================================
head('3. THE DESKTOP CHANGED BY THE BAR COLOUR AND NOTHING ELSE')
# ==========================================================================
# The three colours become the house CATEGORY family, which is muted where
# Bootstrap's were bright - so this is a visible change on a screen nobody
# complained about, and it has to be bounded.
if sync_playwright is None or not OLD:
    skip('the desktop changed by its colour and nothing else',
         'playwright or backup missing')
else:
    def wide(src, depth_class):
        trs = ''.join(
            '<tr class="task-row task-type-%s%s">'
            '<td class="task-name-cell"><div class="task-indent-%d">'
            '<strong class="task-name">%s</strong></div></td>'
            '<td>%s</td><td>In Progress</td></tr>'
            % (t, (' task-depth-%d' % d) if depth_class else '', d, n,
               t.title())
            for t, d, n in ROWS)
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style></head>'
                '<body style="margin:0"><div class="table-container">'
                '<table class="table alv-table task-list-table"><tbody>%s'
                '</tbody></table></div></body></html>'
                % (read(BOOT) if os.path.exists(BOOT) else '',
                   css_of(alv_tree.code_only(now(BASE))), css_of(src), trs))
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(viewport={'width': 1280, 'height': 700})
            pg.set_content(html)
            pg.wait_for_timeout(150)
            r = pg.evaluate("""() => [...document.querySelectorAll(
              'tr.task-row')].map(tr => {
                const rr = tr.getBoundingClientRect();
                const s = getComputedStyle(tr);
                const d = tr.querySelector('[class^=task-indent-]');
                return {t: tr.className.match(/task-type-(\\w+)/)[1],
                        left: Math.round(rr.left), w: Math.round(rr.width),
                        h: Math.round(rr.height),
                        bw: s.borderLeftWidth, bc: s.borderLeftColor,
                        pad: getComputedStyle(d).paddingLeft};})""")
            b.close()
        return r

    a, b2 = wide(was(PAGE), False), wide(now(PAGE), True)
    moved = [(x['t'], k, x[k], y[k]) for x, y in zip(a, b2)
             for k in ('left', 'w', 'h', 'bw', 'pad') if x[k] != y[k]]
    ok(not moved, 'on a desktop nothing moved - position, width, height, '
       'bar width and the name indent are all as they were',
       '\n'.join(str(m) for m in moved[:5]))
    changed = [(x['t'], x['bc'], y['bc']) for x, y in zip(a, b2)
               if x['bc'] != y['bc']]
    ok(len(changed) == 3,
       'and all three bar colours did change, which is the round',
       '\n'.join('%s %s -> %s' % c for c in changed))

# ==========================================================================
head('4. A PROJECT ROW HAS NO ACTIONS - AND A READ-ONLY USER STILL DOES')
# ==========================================================================
# THE GATE THAT KEPT THIS HONEST. The else-branch holding the two disabled
# icons is ALSO what a reader without can_edit_projects sees on a real
# task. Removing it wholesale would have taken their disabled state away
# and left them with nothing, on every row.
i = SRC.index('<td class="desktop-action-cell cell-actions">')
cell = SRC[i:SRC.index('</tr>', i)]
ok('{% if item.task_obj %}' in cell, 'the actions are gated on task_obj')
ok(SRC.count('{% if item.task_obj %}') == 2,
   'both cells are gated - the desktop one and the mobile bar')
ok('icon-disabled' in cell,
   'the disabled pair is still there for a read-only user')
ok('perms.auth.can_edit_projects' in cell,
   '  and so is the permission branch that shows it')
ok('Not available here' in cell or 'available' in cell.lower(),
   '  with the title it always had')
if OLD:
    oi = OLD.index('<td class="desktop-action-cell cell-actions">')
    ok('{% if item.task_obj %}' not in OLD[oi:OLD.index('</tr>', oi)],
       'CONTROL: before this round nothing was gated on task_obj, so a '
       'project row showed two icons that can never be pressed')

# ==========================================================================
head('5. THE COLOURS ARE THE CATEGORY FAMILY, NOT THE SEMANTIC ONE')
# ==========================================================================
# base keeps the two sets apart on purpose, and says so where it declares
# them: a status must not change meaning because a brand colour moved. A
# subtask is not a warning.
b = alv_tree.code_only(now(BASE))
for _k, tag, _d in KINDS:
    ok('--alv-tag-%s-ink' % tag in b,
       'base declares --alv-tag-%s-ink' % tag)
    ok('var(--alv-tag-%s-ink)' % tag in SRC,
       '  and the page uses it')
for wrong in ('--alv-good', '--alv-warn'):
    ok(wrong not in SRC,
       'the page does NOT reach for %s - a type is a category, not a '
       'verdict' % wrong)

# ==========================================================================
head('6. TWENTY-TWO HEXES, AND THE TWO THAT STAY')
# ==========================================================================
left_ = re.findall(r'#[0-9a-fA-F]{3,6}\b',
                   re.sub(r'\{#.*?#\}', '', SRC, flags=re.S))
ok(left_ == ['#000'],
   'the only hex left in the code is the print black', left_)
i = SRC.find('@media print')
ok(i >= 0 and '#000' in SRC[i:],
   '  and it is inside the print block, where a border should be black')

for hexv, token in TOKENS:
    ok(token in SRC, '%-8s -> %s' % (hexv, token))
    if OLD:
        ok(bool(re.search(re.escape(hexv), OLD, re.I)),
           '  CONTROL: the backup used it')

# AND A NOTE THAT RECORDS AN OLD COLOUR STILL RECORDS IT. The page carries
# a comment about a label that had drifted to 11px UPPERCASE #6c757d.
# Rewriting that to name a token would turn the record of a past wrong
# into a description of a present right.
ok('#6c757d' in RAW,
   'the note recording a drifted colour still names it')
ok('#6c757d' not in re.sub(r'\{#.*?#\}', '', SRC, flags=re.S),
   '  while no RULE uses it any more')

# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
