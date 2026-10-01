# -*- coding: utf-8 -*-
"""test_detail_pills.py - Section P round P3, 1 Oct 2026.

Demetri's Projects findings 1-4, all in projects_detail.html:
the Pending pill's colour, the Edit and Delete icons, High/Medium/Low,
and Pending/In Progress/Completed.

TEN BUTTONS IN THREE CLUSTERS became one control at one size. Measured
in Chromium with identical content in each button, which is the only way
to compare them honestly - without Font Awesome an <i> has no size and
every button collapses to its padding:

    before   project  btn-sm btn-info      32x31
             task     btn-sm btn-info      32x31
             subtask  btn-xs btn-info      28x24
    after    all three .icon-action-btn    34x34, and 44x44 on a phone

A CORRECTION THIS SUITE EXISTS PARTLY TO CARRY. I reported three times
that btn-xs is undefined in Bootstrap 4.1.3 and therefore fell back to
plain .btn, rendering the subtask buttons LARGER than their parents. The
first half is true; the conclusion is not. THIS PAGE DEFINED btn-xs
ITSELF - `.btn-xs { padding: 2px 6px; font-size: 11px }` - so the
subtask buttons were deliberately smaller. I had grepped base.html and
the static folder, found nothing, and said "we do not define it" without
reading the page's own stylesheet. Section 4 checks the dead rule is
gone AND states the real numbers, so the wrong version does not outlive
the round.

SIX PILLS on the agreed P2 map, not a new decision:

    Critical -bad | High, Medium -attn | Low -neutral
    Completed -good | In Progress -info | On Hold -attn
    Pending, Not Started, anything else -neutral

AND THE SUBTASK STATUS PILL IS STILL A CONTROL. Clicking it changes the
status. Question 3 on 1 Oct: keep that, and keep a visible hover. A pill
that changes data and looks like a label is worse than a wrong colour.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_detailpills'
ME = 'test_detail_pills.py'
PATCHER = 'apply_detail_pills.py'
PS1 = 'Push-PendingChanges.ps1'
REL = 'projects/projects_detail.html'
EXE = '/opt/pw-browsers/chromium'
BOOT = 'test_fixture_bootstrap413.css'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

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


def css_of(t):
    return re.sub(r'/\*.*?\*/', ' ', '\n'.join(STYLE.findall(t)), flags=re.S)


def markup_of(t):
    """The rendered markup: no scripts, no styles, and NO DJANGO COMMENT.

    The {# #} sentinel this round signs the page with names the very
    classes the round removed - btn-info, btn-danger, alv-pill - so a
    census that leaves it in counts the explanation as if it were the
    thing explained. The first run of this suite reported 7 pills and
    three surviving Bootstrap classes for exactly that reason."""
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


PATH = alv_tree.join(REL.replace('/', os.sep))
now = (as_left_by(PATH, SUFFIX, read) if as_left_by else read(PATH))
was = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else None
base = read(alv_tree.path_of('base.html'))
m, c = markup_of(now), css_of(now)

print('=' * 74)
print('%s - P3, PROJECT DETAIL JOINS THE STANDARD' % ME)
print('=' * 74)

# ==========================================================================
head('1. base DRAWS EVERYTHING THIS ROUND HANDED TO IT')
# ==========================================================================
bcss = css_of(base)
for n in ('.alv-pill', '.alv-pill-good', '.alv-pill-attn', '.alv-pill-bad',
          '.alv-pill-info', '.alv-pill-neutral', '.row-actions',
          '.icon-action-btn'):
    ok(bool(re.search(r'(?<![-\w])' + re.escape(n) + r'\s*\{', bcss)),
       'base draws %s' % n)
ok(bool(re.search(r'(?<![-\w])\.icon-disabled\b', bcss)),
   'base draws .icon-disabled')
# half the argument for converting is the phone target
ok(bool(re.search(r'\.icon-action-btn\s*\{[^}]*width:\s*44px', bcss)),
   '  and gives it a 44px target below 768px')

# ==========================================================================
head('2. NO BOOTSTRAP BUTTON CLASS, NO INLINE DISABLED STYLE')
# ==========================================================================
for dead in ('btn-xs', 'btn-info', 'btn-danger', 'btn-light'):
    ok(not re.search(r'(?<![-\w])' + dead + r'(?![\w-])', m),
       '%-10s is gone from the markup' % dead)
ok('opacity: 0.5' not in m, 'no inline opacity on a disabled twin')
ok('#6c757d' not in m, 'and no inline literal grey on its icon')
ok('fa-edit' not in m,
   'fa-edit is gone - the house glyph is fa-pencil-alt')
ok(m.count('fa-pencil-alt') == 6,
   '  and there are 6 of those: 3 live, 3 twins',
   '%d found' % m.count('fa-pencil-alt'))
ok(m.count('icon-disabled') == 5,
   '5 disabled twins - project 1, task 2, subtask 2',
   '%d found' % m.count('icon-disabled'))
ok(m.count('row-actions') == 4,
   '4 clusters - the project one wraps its if, the subtask has two '
   'branches', '%d found' % m.count('row-actions'))
# question 4
ok('action-secondary btn-sm' not in m,
   'Add Task and Add Subtask kept .action-secondary and lost .btn-sm')
ok(m.count('action-secondary') >= 2, '  and still carry .action-secondary')

# ==========================================================================
head('3. SIX PILLS, ON THE MAP AGREED IN P2')
# ==========================================================================
ok(m.count('alv-pill ') == 6, 'six pill spans',
   '%d found' % m.count('alv-pill '))
# 4 status chains x 1 each, 2 priority chains x 1 each
for tone, n, why in (('alv-pill-good', 4, 'Completed, in 4 status chains'),
                     ('alv-pill-info', 4, 'In Progress'),
                     ('alv-pill-bad', 2, 'Critical, in 2 priority chains'),
                     ('alv-pill-attn', 6, 'On Hold x4 + High/Medium x2'),
                     ('alv-pill-neutral', 6, 'the fallback in all 6')):
    ok(m.count(tone) == n, '%-18s x%d  (%s)' % (tone, n, why),
       '%d found' % m.count(tone))
ok("== 'Completed' %}alv-pill-good" in m, 'Completed is the only -good')
ok("== 'Critical' %}alv-pill-bad" in m, 'Critical is the only -bad')
ok("{% else %}alv-pill-neutral" in m,
   'and Pending, Not Started and anything unforeseen fall to -neutral')
# the private stylesheet went with them
for gone in ('.status-badge', '.status-completed', '.status-pending',
             '.status-on-hold', '.status-not-started', '.priority-critical',
             '.priority-low', '.task-status-badge',
             '.task-priority-indicator'):
    ok(not re.search(re.escape(gone) + r'(?![\w-])[^{}]*\{', c),
       '%-28s is base\'s now' % gone)
# and the LAYOUT it sat in did not
for keep in ('.project-status-container', '.overview-status-col'):
    ok(bool(re.search(re.escape(keep) + r'(?![\w-])[^{}]*\{', c)),
       '%-28s is layout, and stayed' % keep)

# ==========================================================================
head('4. THE btn-xs CORRECTION, MEASURED')
# ==========================================================================
# I said three times that btn-xs was undefined and therefore RENDERED
# LARGER. The page defined it itself. The numbers below are the real
# ones, taken with identical content in each button.
ok(was is not None, 'there is a backup to measure the before against')
if was is not None:
    ok(bool(re.search(r'(?<![-\w])\.btn-xs\s*\{', css_of(was))),
       'the page really did define .btn-xs itself - my claim that nothing '
       'defined it was wrong')
ok(not re.search(r'(?<![-\w])\.btn-xs\s*\{', c),
   '  and that rule is gone now, because nothing wears the class')

try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

BOOTP = os.path.join(ROOT, BOOT)
if not have_pw or not os.path.isfile(BOOTP):
    skip('the button sizes', 'playwright or the bootstrap fixture is absent')
else:
    from playwright.sync_api import sync_playwright
    # A 14px box stands in for the glyph, so the only difference between
    # the buttons is their class. Without it an <i> has no size and every
    # button collapses to its padding - which is how the first cut of the
    # render harness reported btn-xs as SMALLER than it is.
    G = '<span style="display:inline-block;width:14px;height:14px"></span>'
    page = os.path.join(SCRATCH, 'btn.html')
    with open(page, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><meta charset="utf-8"><style>%s</style>'
                 '<style>%s</style><style>%s</style><body>'
                 '<a id="sm" class="btn btn-sm btn-info">%s</a>'
                 '<a id="xs" class="btn btn-xs btn-info">%s</a>'
                 '<a id="ic" class="icon-action-btn icon-edit">%s</a>'
                 '</body>' % (read(BOOTP), '\n'.join(STYLE.findall(base)),
                              css_of(was or now), G, G, G))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 900, 'height': 300})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, page)
        got = {}
        for i in ('sm', 'xs', 'ic'):
            bb = pg.query_selector('#' + i).bounding_box()
            got[i] = (round(bb['width']), round(bb['height']))
        ctx.close()
        br.close()
    print('       btn-sm %s | btn-xs %s | icon-action-btn %s'
          % (got['sm'], got['xs'], got['ic']))
    ok(got['xs'][0] < got['sm'][0] and got['xs'][1] < got['sm'][1],
       'btn-xs was SMALLER than btn-sm, not larger - the correction',
       'btn-xs %s against btn-sm %s' % (got['xs'], got['sm']))
    ok(got['ic'] == (34, 34),
       '  and the house control is 34x34, one size for all three clusters',
       'it is %s' % (got['ic'],))

# ==========================================================================
head('5. THE SUBTASK STATUS PILL IS STILL A CONTROL')
# ==========================================================================
ok('editTaskStatus(' in m, 'clicking it still changes the status')
ok('clickable-status' in m, '  and it keeps the .clickable-status hook')
ok(bool(re.search(r'\.clickable-status\s*\{[^}]*cursor:\s*pointer', c)),
   '  which still gives it a pointer cursor')
hov = re.search(r'\.clickable-status:hover\s*\{([^}]*)\}', c)
ok(hov is not None, '  and a hover')
if hov:
    ok('#007bff' not in hov.group(1),
       '    on the house accent, not Bootstrap blue')
    ok('var(--alv-accent' in hov.group(1),
       '    - a token, not a literal', hov.group(1)[:70])
ok('Click to change the status' in m,
   '  and it says so in a title, for anyone who does not hover')

# ==========================================================================
head('6. NOT THIS ROUND - THE OTHER TWO PROJECTS PAGES')
# ==========================================================================
# projects.html and project_gantt.html carry the same three .status-*
# colours. They are named here so "the Projects pills are done" is not
# read off this suite passing.
left = []
for rel in ('projects/projects.html', 'projects/project_gantt.html'):
    p = alv_tree.join(rel.replace('/', os.sep))
    if not os.path.isfile(p):
        continue
    if re.search(r'\.status-pending\s*\{', css_of(read(p))):
        left.append(rel)
ok(len(left) == 2,
   'both of the other Projects pages still carry their own .status-* '
   'colours, and are a round of their own',
   'found %s' % left)
for rel in left:
    print('       %s' % rel)

# ==========================================================================
head('7. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ok(os.path.isfile(PATH + SUFFIX), 'the round left its backup')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
