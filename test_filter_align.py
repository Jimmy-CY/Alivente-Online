# -*- coding: utf-8 -*-
"""test_filter_align.py - Section FA round FA-1, 4 Oct 2026.

Demetri, of the Projects filter panel: "The filters are not in line...."

==========================================================================
HE SAW ONE PAGE. IT WAS TEN
==========================================================================
Rendered at 1280 before this round, ten of the seventeen panels that
render had their controls at two different heights - eight of them by
2px, which is the gap between an <input> and a <select>, and Projects by
25px, which is the height of a search hint.

ONE DECLARATION CAUSED ALL TEN:

    .filter-grid { align-items: end; }

end aligns the BOTTOMS of the groups, and a group is a label above a
control, so its bottom is the control's bottom. The instant two groups
differ in height their tops part. Projects differed most because its
Search group has a hint UNDER the control, so the group's bottom was the
hint's bottom and the whole group rose 25px to put it level.

==========================================================================
THIS SUITE MEASURES, IT DOES NOT READ
==========================================================================
Section 1 renders EVERY filter panel in the tree twice - under base as
the backup left it, and under base as it is now - and reports the top of
every label and every control in each. The claim is not "the file says
start"; it is "seventeen panels, every label top 0, every control top
27". A rule that is present and loses to a page's own would read fine
and measure wrong.

Section 2 holds the thing that makes aligning labels enough: every
.filter-label in the tree is one line. The day one wraps, aligning the
label tops stops aligning the control tops, and this says so before a
screenshot does.
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

SUFFIX = '.bak_filteralign'
ME = 'test_filter_align.py'
PATCHER = 'apply_filter_align.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_filteralign_')

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
SRC = alv_tree.code_only(now(BASE))
OLD = alv_tree.code_only(was(BASE)) if was(BASE) else ''


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def grid_rules(css):
    return re.findall(r'\.filter-grid[^{]*\{[^}]*\}', css)


# EVERY FILTER PAGE, BY THE TREE'S OWN CENSUS. house_filter_pages returns
# basenames and projects.html lives in a subfolder, so it is resolved
# against templates() rather than path_of, which takes a basename and
# raises on a nested one.
PAGES = []
for nm in alv_tree.house_filter_pages():
    hits = [q for q in alv_tree.templates()
            if os.path.basename(q) == os.path.basename(nm)]
    if hits:
        PAGES.append(hits[0])


def detag(s):
    s = re.sub(r'\{%\s*(if|else|elif|endif|for|empty|endfor|csrf_token|'
               r'url|static|block|endblock|load|include|with|endwith)'
               r'[^%]*%\}', '', s)
    s = re.sub(r'\{\{[^}]*\}\}', 'x', s)
    return re.sub(r'\{#.*?#\}', '', s, flags=re.S)


def panel_of(src):
    m = re.search(r'<div class="filter-grid"[^>]*>.*?\n\s*</div>\s*\n\s*</form>',
                  src, re.S)
    if not m:
        m = re.search(r'<div class="filter-grid"[^>]*>.*', src, re.S)
    return detag(m.group(0)) if m else ''


# ==========================================================================
head('1. EVERY PANEL IN THE TREE, MEASURED AT 1280')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def measure(basecss):
    out = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for p in PAGES:
            name = alv_tree.rel(p).replace(os.sep, '/')
            src = alv_tree.code_only(now(p))
            panel = panel_of(src)
            if not panel:
                continue
            html = ('<!doctype html><html><head><meta charset="utf-8">'
                    '<style>%s</style><style>%s</style><style>%s</style>'
                    '</head><body style="margin:0;padding:0">'
                    '<div class="alv-filter is-open" style="width:1200px">%s'
                    '</div></body></html>'
                    % (read(BOOT), basecss, css_of(src), panel))
            pg = b.new_page(viewport={'width': 1280, 'height': 1000})
            pg.set_content(html)
            pg.wait_for_timeout(80)
            out[name] = pg.evaluate("""() => {
              const r = [];
              for (const g of document.querySelectorAll('.filter-group')) {
                const l = g.querySelector('.filter-label');
                const c = g.querySelector('select, input, textarea');
                r.push({
                  label: l ? l.textContent.trim().split('\\n')[0].slice(0,20) : '-',
                  lt: l ? Math.round(l.getBoundingClientRect().top) : -1,
                  lh: l ? Math.round(l.getBoundingClientRect().height) : -1,
                  ct: c ? Math.round(c.getBoundingClientRect().top) : -1,
                  cw: c ? Math.round(c.getBoundingClientRect().width) : -1,
                  gw: Math.round(g.getBoundingClientRect().width)});
              }
              return r;
            }""")
            pg.close()
        b.close()
    return out


def crooked(m):
    return sorted(n for n, r in m.items()
                  if len({x['ct'] for x in r if x['ct'] >= 0}) > 1)


if sync_playwright is None or not OLD:
    for _ in range(7):
        skip('the panels at 1280', 'playwright or backup missing')
    after = {}
else:
    before = measure(css_of(OLD))
    # css_of, NOT the file. The first run of this suite handed measure()
    # the whole of base.html - markup and all - as a stylesheet, and the
    # CSS parser gave up at the first tag. The panels then rendered with
    # no base styling, every y was 499 instead of 27, and section 1 said
    # "none of them is crooked now" because unstyled groups are all the
    # same height. A measurement with no stylesheet in it proves nothing
    # and looks like a pass.
    after = measure(css_of(SRC))
    bad_before = crooked(before)
    bad_after = crooked(after)
    print('   panels measured: %d' % len(after))
    for n in sorted(after):
        tops = sorted({x['ct'] for x in after[n] if x['ct'] >= 0})
        was_tops = sorted({x['ct'] for x in before.get(n, [])
                           if x['ct'] >= 0})
        print('   %-40s before=%-12s after=%s'
              % (n, was_tops, tops))

    ok(len(after) >= 17, 'at least 17 panels rendered', len(after))
    ok(set(before) == set(after),
       '  the same panels in both runs - nothing dropped out of the census')
    ok(len(bad_before) == 10,
       'CONTROL: %d panels had their controls at two heights BEFORE'
       % len(bad_before), '\n'.join(bad_before))
    ok('projects/projects.html' in bad_before,
       '  Projects among them - the page Demetri reported')
    ok(not bad_after, 'and none of them does now',
       '\n'.join(bad_after))

    tops = sorted({x['ct'] for r in after.values() for x in r if x['ct'] >= 0})
    ok(tops == [27],
       'every control in every panel starts at the same y: %s' % tops)
    ltops = sorted({x['lt'] for r in after.values() for x in r if x['lt'] >= 0})
    ok(ltops == [0], '  and every label at %s' % ltops)

# ==========================================================================
head('2. WHICH ONLY WORKS WHILE A LABEL IS ONE LINE')
# ==========================================================================
# Aligning the label TOPS aligns the control tops because every label is
# the same height. That is a fact about this tree today, not a law, so
# it is measured rather than assumed: the day a label wraps, the controls
# part company again and this is what says so.
if not after:
    skip('the label heights', 'nothing rendered')
else:
    hs = sorted({x['lh'] for r in after.values() for x in r if x['lh'] >= 0})
    ok(hs == [21],
       'every .filter-label in the tree is one line: %s' % hs,
       'a label taller than the rest pushes its own control down again')

# ==========================================================================
head('3. BASE SAYS IT ONCE, AND SAYS start')
# ==========================================================================
rules = grid_rules(SRC)
aligns = [r for r in rules if 'align-items' in r]
ok(len(aligns) == 1,
   'base declares .filter-grid alignment exactly once',
   '\n'.join(aligns))
ok(aligns and 'align-items: start' in aligns[0],
   '  and it is start')
if OLD:
    oldal = [r for r in grid_rules(OLD) if 'align-items' in r]
    ok(oldal and 'align-items: end' in oldal[0],
       '  CONTROL: the backup said end')
# AND NO PAGE OVERRIDES IT, which would put that page back where it was.
over = []
for p in PAGES:
    for r in grid_rules(alv_tree.code_only(now(p))):
        if 'align-items' in r and 'start' not in r:
            over.append('%s: %s' % (alv_tree.rel(p).replace(os.sep, '/'),
                                    ' '.join(r.split())))
ok(not over, 'and no page overrides it back', '\n'.join(over))

# THE ONE PANEL THAT WROTE ITS OWN ALIGNMENT CHOSE start. recipe_management
# builds a .recipe-filter-grid of its own rather than using .filter-grid,
# and it has said align-items: start since it was written - which is the
# same answer this round reaches, arrived at independently.
rec = [p for p in alv_tree.templates()
       if os.path.basename(p) == 'recipe_management.html']
if rec:
    rsrc = alv_tree.code_only(now(rec[0]))
    m = re.search(r'\.recipe-filter-grid\s*\{[^}]*\}', rsrc)
    ok(m is not None and 'align-items: start' in m.group(0),
       'and the one page that wrote its own grid had already chosen start')

# ==========================================================================
head('4. PROJECTS TAKES BASE\'S COLUMNS')
# ==========================================================================
proj = [p for p in alv_tree.templates()
        if alv_tree.rel(p).replace(os.sep, '/') == 'projects/projects.html'][0]
P = alv_tree.code_only(now(proj))
PW = alv_tree.code_only(was(proj)) if was(proj) else ''
def own_columns(css):
    """The rules that set a DESKTOP track list.

    The phone rule - grid-template-columns: 1fr - is on every one of
    these pages and is not drift; base sets the same thing itself under
    768. Matched exactly, because '1fr;' as a substring also matches
    '2fr 1fr 1fr;' and the first version of this census counted one
    page where there are twelve."""
    out = []
    for r in grid_rules(css):
        m = re.search(r'grid-template-columns\s*:\s*([^;]+);', r)
        if m and m.group(1).strip() != '1fr':
            out.append(r)
    return out


desk = own_columns(P)
ok(not [r for r in desk if '2fr' in r],
   'projects.html no longer sets 2fr 1fr 1fr',
   '\n'.join(' '.join(r.split()) for r in desk))
if PW:
    ok(any('2fr 1fr 1fr' in r for r in grid_rules(PW)),
       '  CONTROL: the backup did')
if after and 'projects/projects.html' in after:
    # THE GROUP, not the control inside it. The Search group holds an
    # input AND the magnifying-glass button, so its input measures 208
    # beside two 240px selects while all three TRACKS are 240 - which is
    # the thing Demetri asked for. Measuring the control reported a
    # difference the page does not have.
    ws = sorted({x['gw'] for x in after['projects/projects.html']})
    ok(len(ws) == 1,
       '  and its three fields are now one width: %s' % ws,
       'Demetri, asked: "No - all three the same."')
    ok(ws and ws[0] <= 240,
       '  at or under base\'s 240px cap: %s' % ws)

# THE OTHER TWELVE ARE NOT TOUCHED, and the number is held here so it
# cannot drift unnoticed.
still = []
for p in PAGES:
    if os.path.abspath(p) == os.path.abspath(proj):
        continue
    if own_columns(alv_tree.code_only(now(p))):
        still.append(alv_tree.rel(p).replace(os.sep, '/'))
print('   pages still setting their own columns: %d' % len(still))
for n in sorted(still):
    print('     %s' % n)
ok(len(still) == 11,
   '%d pages still set their own track list - out of scope, not forgotten'
   % len(still), '\n'.join(sorted(still)))

# ==========================================================================
head('5. REGISTERED')
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
