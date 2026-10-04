# -*- coding: utf-8 -*-
"""test_row_action_order.py - Section RA round RA-1, 4 Oct 2026.

Demetri, of the Tenants list: "I think that we should put the Delete
Action Item on the right hand side of all the icons. We should define a
standard order that we place all icons in all tables, in the Action
Column and apply this across the app."

    LOOK -> CHANGE -> COPY -> ADVANCE -> DESTROY

==========================================================================
WHAT THIS ASKS, AND OF WHAT
==========================================================================
Section 1 reads EVERY .row-actions wrapper in the tree and requires the
order. Not the five pages the round changed - every one, so a page added
next month is judged by the same rule without this file being edited.

Section 2 asks a question the round discovered it had to ask. base states
the rule three times, beside .icon-duplicate, .icon-manage and
.icon-list - "a class carries ONE PICTURE" - and .icon-view was carrying
four: fa-eye, fa-file-contract, fa-box and fa-file-pdf. It matters here
and not only tidily, because the ORDER SORTS ON THE NAME: a lease
agreement wearing .icon-view sorts as "view this record" and lands in
the wrong place inside Look.

AND THE FIRST BUILD OF THIS ROUND FAILED THAT GATE. It put both document
glyphs on one new .icon-document and hung fa-box on the existing
.icon-list beside fa-shopping-cart - repairing a class that carried four
pictures by creating two that carried two. Asking the question of every
class rather than of .icon-view is what caught it.

Section 3 renders the Tenants row in a browser, before and after, and
reads the left-to-right order off the screen. A rule the source obeys
and the page does not would pass every text check in this file.
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
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree
import alv_rowactions as RA

SUFFIX = '.bak_rowactorder'
ME = 'test_row_action_order.py'
PATCHER = 'apply_row_action_order.py'
REPORT = 'Show-RowActionDrift.py'
RULE = 'alv_rowactions.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_rowact_')

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
            for line in str(detail).split('\n')[:10]:
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


BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
TENANT = alv_tree.path_of('tenant.html')


def scan(getter):
    """[(page, seq, unfixable)] and {class: {glyphs}} over the tree."""
    rows, glyphs = [], {}
    for p in sorted(alv_tree.templates()):
        name = alv_tree.rel(p).replace(os.sep, '/')
        src = alv_tree.code_only(getter(p))
        for s, e, inner in RA.wrappers(src):
            seq = RA.sequence(inner)
            if seq:
                rows.append((name, seq, RA.unfixable(inner)))
            for m in re.finditer(
                    r'class="([^"]*icon-action-btn[^"]*)"[^>]*>\s*'
                    r'<i class="[^"]*?(fa-[a-z0-9-]+)', inner, re.S):
                for c in m.group(1).split():
                    if c.startswith('icon-') and c not in (
                            'icon-action-btn', 'icon-disabled'):
                        glyphs.setdefault(c, set()).add(m.group(2))
                        break
    return rows, glyphs


ROWS, GLYPHS = scan(now)
OLDROWS, OLDGLYPHS = scan(lambda p: was(p) or now(p))

# ==========================================================================
head('1. EVERY ACTION COLUMN IN THE TREE IS IN HOUSE ORDER')
# ==========================================================================
multi = [(n, s) for n, s, _ in ROWS if len(s) >= 2]
out = [(n, s) for n, s in multi if not RA.in_order(s)]
print('   %d wrapper(s), %d with two or more actions'
      % (len(ROWS), len(multi)))
ok(len(multi) >= 20,
   'there are %d multi-action columns to judge' % len(multi))
ok(not out, 'and every one reads Look, Change, Copy, Advance, Destroy',
   '\n'.join('%s: %s' % (n, ' -> '.join(s)) for n, s in out))
ok(all(s[-1] == 'delete' for _, s in multi if 'delete' in s),
   'Delete is LAST wherever it appears - which is what was asked for',
   '\n'.join('%s: %s' % (n, ' -> '.join(s)) for n, s in multi
             if 'delete' in s and s[-1] != 'delete'))

oldmulti = [(n, s) for n, s, _ in OLDROWS if len(s) >= 2]
oldout = [(n, s) for n, s in oldmulti if not RA.in_order(s)]
ok(len(oldout) == 5,
   'CONTROL: %d columns were out of order before this round' % len(oldout),
   '\n'.join('%s: %s' % (n, ' -> '.join(s)) for n, s in oldout))
ok(any(n == 'tenant.html' and s.index('delete') < len(s) - 1
       for n, s in oldout),
   '  tenant.html among them, with Delete second of four - the row '
   'Demetri was looking at')

# AND NO PAIR IS STUCK INSIDE ONE BLOCK. crs/country_list writes Edit and
# Delete inside a single {% if perms %}; sorting blocks cannot separate
# them, so if such a pair is ever out of order it has to be done by hand
# and this is what says so.
stuck = [(n, u) for n, _, u in ROWS if u]
ok(not stuck,
   'and no two actions share a permission test in the wrong order',
   '\n'.join('%s: %s' % (n, u) for n, u in stuck))

# ==========================================================================
head('2. ONE NAME, ONE PICTURE')
# ==========================================================================
for c in sorted(GLYPHS):
    print('   %-20s %s' % (c, ', '.join(sorted(GLYPHS[c]))))
two = {c: g for c, g in GLYPHS.items() if len(g) > 1}
ok(not two,
   'every icon class in the tree carries exactly one picture',
   '\n'.join('%s: %s' % (c, ', '.join(sorted(g))) for c, g in two.items()))
ok(GLYPHS.get('icon-view') == {'fa-eye'},
   '  .icon-view draws fa-eye and nothing else')
oldtwo = {c: g for c, g in OLDGLYPHS.items() if len(g) > 1}
ok('icon-view' in oldtwo and len(oldtwo['icon-view']) == 4,
   'CONTROL: before this round .icon-view carried %d pictures'
   % len(oldtwo.get('icon-view', [])),
   ', '.join(sorted(oldtwo.get('icon-view', []))))
# base has to DEFINE the three new names, or they are classes with no
# rules and the buttons lose their colour entirely.
B = alv_tree.code_only(now(BASE))
for c in ('icon-document', 'icon-pdf', 'icon-assets'):
    ok(re.search(r'\.%s\b[^{]*[,{]' % c, B) is not None,
       '  base defines .%s' % c)
ok(not re.search(r'\.icon-(document|pdf|assets)\s*\{[^}]*#[0-9a-f]{3}',
                 B, re.I),
   '  and all three are NAMES on an existing colour, not new hexes')

# ==========================================================================
head('3. THE TENANTS ROW, IN A BROWSER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def strip_django(s):
    # The IF arm, which is what a user with permission sees.
    s = re.sub(r'\{%\s*else\s*%\}.*?\{%\s*endif\s*%\}', '', s, flags=re.S)
    s = re.sub(r'\{%[^%]*%\}', '', s)
    s = re.sub(r'\{\{[^}]*\}\}', 'x', s)
    return re.sub(r'\{#.*?#\}', '', s, flags=re.S)


def onscreen(src, basecss):
    w = RA.wrappers(alv_tree.code_only(src))
    if not w:
        return []
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style></head>'
            '<body style="margin:0;padding:8px">'
            '<table class="table alv-table"><tbody><tr>'
            '<td class="desktop-action-cell cell-actions">'
            '<span class="row-actions">%s</span></td></tr></tbody></table>'
            '</body></html>'
            % (read(BOOT),
               '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                    basecss, re.S | re.I)),
               strip_django(w[0][2])))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1280, 'height': 400})
        pg.set_content(html)
        pg.wait_for_timeout(120)
        r = pg.evaluate("""() => [...document.querySelectorAll(
              '.row-actions .icon-action-btn')]
            .map(e => ({x: Math.round(e.getBoundingClientRect().left),
                        cls: [...e.classList].find(c =>
                             c.startsWith('icon-') && c !== 'icon-action-btn'),
                        t: (e.getAttribute('title')||'').slice(0,24)}))
            .sort((a,b) => a.x - b.x)""")
        b.close()
    return r


if sync_playwright is None or not was(TENANT):
    for _ in range(4):
        skip('the Tenants row on screen', 'playwright or backup missing')
else:
    before = onscreen(was(TENANT), was(BASE) or now(BASE))
    after = onscreen(now(TENANT), now(BASE))
    print('   BEFORE  %s' % ' -> '.join('%s(%s)' % (b['cls'], b['x'])
                                        for b in before))
    print('   AFTER   %s' % ' -> '.join('%s(%s)' % (a['cls'], a['x'])
                                        for a in after))
    bseq = [b['cls'] for b in before]
    aseq = [a['cls'] for a in after]
    ok(len(aseq) == len(bseq) and len(aseq) >= 4,
       'the same %d controls are on the row' % len(aseq),
       '%s vs %s' % (bseq, aseq))
    ok(bseq and bseq.index('icon-delete') == 1,
       'CONTROL: Delete was SECOND on screen, of %d' % len(bseq),
       ' -> '.join(bseq))
    ok(aseq and aseq[-1] == 'icon-delete',
       'and it is last on screen now', ' -> '.join(aseq))
    ok(aseq[:2] == ['icon-view', 'icon-document'],
       '  with the eye and the lease agreement leading, in that order',
       ' -> '.join(aseq))
    ok(sorted(set(bseq)) != sorted(set(aseq)),
       '  and the lease agreement is no longer classed as a plain view',
       'before %s / after %s' % (sorted(set(bseq)), sorted(set(aseq))))

# ==========================================================================
head('4. THE RULE IS WRITTEN ONCE')
# ==========================================================================
# Three callers ask it - the patcher, the report and this file. A rule
# each of them spelled out would be three rules inside a month.
ok(os.path.isfile(os.path.join(ROOT, RULE)), '%s is on disk' % RULE)
for f in (PATCHER, REPORT, ME):
    src = read(os.path.join(ROOT, f))
    ok('alv_rowactions' in src, '  %s asks it rather than restating it' % f)
ok(sorted(RA.FAMILY_NAME.values()) ==
   sorted(['look', 'change', 'copy', 'advance', 'destroy']),
   'the five families are look, change, copy, advance, destroy')
ok(RA.FAMILY['delete'] == max(RA.FAMILY.values()),
   '  and destroy sorts last, which is the thing that was asked for')

# ==========================================================================
head('5. THE REPORT RUNS, AND CAN FAIL')
# ==========================================================================
import subprocess
r = subprocess.run([sys.executable, REPORT, '--strict'],
                   capture_output=True, text=True, cwd=ROOT)
ok(r.returncode == 0, '%s --strict passes' % REPORT,
   (r.stdout or '') + (r.stderr or ''))
ok('Every action column is in house order' in r.stdout,
   '  and says so')
# CONTROL - a drifted wrapper has to be caught. Built here rather than
# asserted: a report that cannot fail is a report that says nothing.
bad = '<span class="row-actions">' \
      '<a class="icon-action-btn icon-delete"><i class="fas fa-trash"></i></a>' \
      '<a class="icon-action-btn icon-edit"><i class="fas fa-pencil-alt"></i></a>' \
      '</span>'
w = RA.wrappers(bad)
ok(len(w) == 1 and RA.sequence(w[0][2]) == ['delete', 'edit'],
   'CONTROL: a delete-then-edit row reads as %s'
   % RA.sequence(w[0][2]) if w else 'CONTROL: the probe parsed')
ok(w and not RA.in_order(RA.sequence(w[0][2])),
   '  and the rule calls it out of order')
ok(w and RA.sequence(RA.ordered(w[0][2])) == ['edit', 'delete'],
   '  and puts it right')

# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(REPORT in ps, '  and %s runs in the sweep' % REPORT)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
