# -*- coding: utf-8 -*-
"""test_task_table.py - Section P round P2, 1 Oct 2026.

projects/project_task_list.html had rebuilt base's table standard under
its own class name: 23 rules, 77 declarations on .task-list-table, six of
them a straight rename of a rule base already owned - and one of them had
DRIFTED, which is the whole argument against a private copy:

    base   .alv-table td::before          12.5px, sentence case,
                                          var(--alv-ink-soft)
    page   td[data-label]::before          11px, UPPERCASE, .4px tracking,
                                          #6c757d

Measured in Chromium at 386px, on the page itself:

    before   11px   uppercase   rgb(108, 117, 125)
    after    12.5px none        rgb(91, 107, 115)

SECTION 3 IS THE CLAIM. It is a render rather than a reading because the
question is not "is the rule gone" but "what does the browser now draw",
and those are different questions - the page's block renders after
base's, so at equal specificity the page was winning.

THE SCREEN ALSO HAD NO WAY TO ACT ON A ROW. Six columns, no Edit, no
Delete, no mobile action bar. Demetri agreed to add one on 1 Oct, with
disabled twins on the project row because a project is not edited from
here. The discriminator is item.task_obj: the view puts task_obj on task
and subtask rows and project_obj on the project row, so asking for
task_obj asks whether there is a task to edit.

AND THE EXPORT. The page sends the table to Excel by reading every th and
td. Two new cells per row would have put a blank column and a column
reading "Edit Delete" into the spreadsheet, and left !cols describing six
columns of an eight-column sheet. Section 7 runs the page's own selector
against the page's own table and counts what comes back.
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

SUFFIX = '.bak_tasktable'
ME = 'test_task_table.py'
PATCHER = 'apply_task_table.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = 'test_fixture_bootstrap413.css'
REL = 'projects/project_task_list.html'
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
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


def js_of(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', t, re.S))


PATH = alv_tree.join(REL.replace('/', os.sep))
now = (as_left_by(PATH, SUFFIX, read) if as_left_by else read(PATH))
was = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else None
base = read(alv_tree.path_of('base.html'))

print('=' * 74)
print('%s - P2, THE TASK LIST JOINS THE TABLE STANDARD' % ME)
print('=' * 74)

# ==========================================================================
head('1. base OWNS EVERY NAME THIS ROUND HANDED TO IT')
# ==========================================================================
# A round that deletes a page rule is only safe if something else draws
# it. These are the names the page stopped defining for itself.
bcss = css_of(base)
for name, rx in (
        ('.alv-table', r'(?<![-\w])\.alv-table\s*\{'),
        ('.alv-table thead th', r'(?<![-\w])\.alv-table thead th\s*\{'),
        ('.alv-table td::before', r'(?<![-\w])\.alv-table td::before\s*\{'),
        ('.alv-table tbody td:first-child',
         r'(?<![-\w])\.alv-table tbody td:first-child\s*\{'),
        ('.alv-stats', r'(?<![-\w])\.alv-stats\s*\{'),
        ('.alv-stat-value', r'(?<![-\w])\.alv-stat-value\s*\{'),
        ('.alv-pill', r'(?<![-\w])\.alv-pill\s*\{'),
        ('.row-actions', r'(?<![-\w])\.row-actions\s*\{'),
        ('.icon-action-btn', r'(?<![-\w])\.icon-action-btn\s*\{'),
        ('.mobile-action-bar.cols-2',
         r'(?<![-\w])\.mobile-action-bar\.cols-2\s*\{')):
    ok(bool(re.search(rx, bcss)), 'base draws %s' % name)
# all five pill tones, because the round uses every one of them
for tone in ('good', 'attn', 'bad', 'info', 'neutral'):
    ok(bool(re.search(r'(?<![-\w])\.alv-pill-%s\s*\{' % tone, bcss)),
       '  and .alv-pill-%s' % tone)

# ==========================================================================
head('2. THE TABLE IS A HOUSE TABLE, AND KEEPS NO PRIVATE COPY')
# ==========================================================================
m = markup_of(now)
c = css_of(now)
ok('<table class="table alv-table task-list-table">' in m,
   'the table is .alv-table')
ok('table-striped' not in m,
   'and does not stripe - of 43 house tables in the tree, one did')

# Nothing base owns may still be defined under the page's own class. The
# token guard matters: .task-list-table td would otherwise match inside
# .task-list-table td.cell-type and report a false pass.
for gone in ('thead th', 'td[data-label]::before', 'td.task-name-cell',
             'td.cell-type', 'td.cell-start-date'):
    ok('.task-list-table ' + gone not in c,
       '.task-list-table %-26s is base\'s now' % gone)
for gone in ('.summary-stat', '.stat-number', '.stat-label'):
    ok(not re.search(re.escape(gone) + r'(?![\w-])[^{}]*\{', c),
       '%-16s is base\'s .alv-stat* now' % gone)

# .task-summary SURVIVES, with exactly one job: the column count.
rules = re.findall(r'\.task-summary(?![\w-])[^{}]*\{([^}]*)\}', c)
ok(len(rules) == 1 and '--alv-stats-cols' in rules[0],
   '.task-summary keeps one rule, carrying --alv-stats-cols',
   '%d rule(s): %s' % (len(rules), rules))

# WHAT THE PAGE STILL OWNS, and should. A round that took these would
# have been taking the page's own design, not base's standard.
for keep in ('.task-indent-1', '.task-description', '.project-icon',
             '.date-value'):
    ok(bool(re.search(re.escape(keep) + r'(?![\w-])[^{}]*\{', c)),
       '%-20s is still the page\'s own' % keep)

# ==========================================================================
head('3. THE PHONE CARD LABEL IS BASE\'S - MEASURED, NOT READ')
# ==========================================================================
# The claim is about what Chromium draws, and the page's style block
# renders AFTER base's, so at equal specificity the page was winning.
# Reading the stylesheet cannot answer that; the browser can.


def fixture(src):
    """The page's styles over base's, with one labelled cell."""
    b = read(os.path.join(ROOT, BOOT)) if os.path.isfile(
        os.path.join(ROOT, BOOT)) else ''
    page = '\n'.join(STYLE.findall(src))
    cls = ('table alv-table task-list-table' if 'alv-table' in markup_of(src)
           else 'table table-striped task-list-table')
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>'
            '<style>%s</style></head><body class="has-sidebar">'
            '<div class="main-content with-sidebar">'
            '<div class="task-list-container"><table class="%s">'
            '<thead><tr><th>Task Name</th><th>Type</th><th>Status</th>'
            '</tr></thead><tbody>'
            '<tr class="task-row task-type-task">'
            '<td class="task-name-cell" data-label="Name">'
            '<strong class="task-name">Strip the existing tiles</strong>'
            '</td>'
            '<td class="cell-type" data-label="Type">'
            '<span class="alv-pill alv-pill-neutral">TASK</span></td>'
            '<td class="cell-status" data-label="Status">'
            '<span class="alv-pill alv-pill-good">Completed</span></td>'
            '</tr></tbody></table></div></div></body></html>'
            % (b, '\n'.join(STYLE.findall(base)), page, cls))


def label_style(src, tag):
    """font-size, text-transform and colour of the card label at 386px."""
    from playwright.sync_api import sync_playwright
    fx = os.path.join(SCRATCH, 'fx_%s.html' % tag)
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(fixture(src))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 386, 'height': 700})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        out = pg.evaluate(
            "() => { const td = document.querySelector('.cell-status');"
            " const s = getComputedStyle(td, '::before');"
            " return [s.fontSize, s.textTransform, s.color,"
            "         s.letterSpacing]; }")
        br.close()
    return out


HOUSE = ('12.5px', 'none')
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

if not have_pw:
    skip('the card label', 'playwright is not installed')
elif was is None:
    skip('the card label', 'no %s backup to compare against' % SUFFIX)
else:
    a = label_style(now, 'after')
    b4 = label_style(was, 'before')
    print('  before  %s' % (b4,))
    print('  after   %s' % (a,))
    ok(a[0] == HOUSE[0], 'the label is %s, the house size' % HOUSE[0],
       'it is %s' % a[0])
    ok(a[1] == HOUSE[1], 'and sentence case, not uppercase',
       'text-transform is %s' % a[1])
    ok(a[2] != b4[2], 'and a different grey from the one it had',
       'before %s, after %s' % (b4[2], a[2]))
    ok(b4[0] != HOUSE[0] or b4[1] != HOUSE[1],
       '  (the backup really did differ, so this is not a tautology)',
       'the before was already %s' % (b4,))

# ==========================================================================
head('4. THE ACTIONS COLUMN')
# ==========================================================================
ok(m.count('desktop-action-cell') == 2,
   'one Actions header and one Actions cell',
   '%d found' % m.count('desktop-action-cell'))
ok(m.count('mobile-action-bar cols-2') == 1,
   'and one two-up phone bar')
ok('fa-edit' not in m,
   'the glyph is not fa-edit - P1 shipped that and test_row_personal '
   'caught it')
ok(m.count('fa-pencil-alt') == 4,
   'fa-pencil-alt four times: desktop live and twin, phone live and twin',
   '%d found' % m.count('fa-pencil-alt'))
ok(m.count('icon-disabled') == 2,
   'two disabled twins, so the cluster is one width on every row')
# THE DISCRIMINATOR. A project row has project_obj and no task_obj, so
# asking for task_obj asks whether there is a task to edit at all.
ok(m.count('item.task_obj and perms.auth.can_edit_projects') == 2,
   'both clusters ask for item.task_obj AND the edit permission')
for name in ('project_tasks_edit', 'project_tasks_delete'):
    ok(name in m, 'the row links %s' % name)
# the url names must exist, or the page 500s on render
up = os.path.join(ROOT, 'pages', 'urls.py')
if os.path.isfile(up):
    urls = read(up)
    for name in ('project_tasks_edit', 'project_tasks_delete'):
        ok("name='%s'" % name in urls, '  and %s is a real url name' % name)
else:
    skip('the url names', 'pages/urls.py not on disk')
# the empty state spans the new width, the way projects.html does
ok('colspan="8"' in m, 'the empty state spans the widened row')

# ==========================================================================
head('5. THE PILLS - FOUR PRIORITIES, FOUR STATUSES, AGREED 1 OCT')
# ==========================================================================
# Critical alone on -bad; High and Medium share -attn because there are
# four priorities and three honest tones; Low -neutral. Completed -good,
# In Progress -info, On Hold -attn, Pending (and anything unforeseen)
# -neutral. -attn is therefore used TWICE, on purpose.
for tone, n in (('alv-pill-bad', 1), ('alv-pill-attn', 2),
                ('alv-pill-good', 1), ('alv-pill-info', 1),
                ('alv-pill-neutral', 3)):
    ok(m.count(tone) == n, '%-18s appears %d time(s)' % (tone, n),
       '%d found' % m.count(tone))
ok("item.priority == 'Critical' %}alv-pill-bad" in m,
   'Critical is the only priority on -bad')
ok("item.status == 'Completed' %}alv-pill-good" in m,
   'Completed is the only status on -good')
# THE TYPE BADGE LOST ITS COLOUR. Project/Task/Subtask is a category and
# base's pills are semantic, so there was no honest tone for it - and the
# row already carries an icon and an indent saying the same thing.
ok('<span class="alv-pill alv-pill-neutral">' in m,
   'the type badge is neutral - the icon and the indent already say it')
# The private badge stylesheet went with the markup that used it: the
# shared rule, the three type colours, the four priorities and the four
# statuses, and 14 literal hexes.
for dead in ('.type-badge', '.priority-badge', '.status-badge',
             '.type-project', '.priority-critical', '.status-completed',
             '.status-pending'):
    ok(not re.search(re.escape(dead) + r'(?![\w-])[^{}]*\{', c),
       '%-20s is gone from the page' % dead)
for dead in ('type-badge', 'priority-badge', 'status-badge'):
    ok(dead not in m,
       '  and %-16s is not left in the markup unstyled' % dead)

# ==========================================================================
head('6. SEVEN COLUMNS, AND THEY SUM TO 100')
# ==========================================================================
# projects.html declared eight columns summing to 110 until P1. Nobody
# noticed, because the browser normalises it - which is exactly why it is
# asserted rather than eyeballed.
got = [(int(x.group(1)), float(x.group(2))) for x in re.finditer(
    r'\.task-list-table th:nth-child\((\d)\)[^{}]*\{[^}]*width:\s*([\d.]+)%',
    c)]
ok(sorted(n for n, _ in got) == [1, 2, 3, 4, 5, 6, 7],
   'every one of the seven columns has a width',
   'found %s' % sorted(n for n, _ in got))
ok(abs(sum(w for _, w in got) - 100) < 0.001,
   'and they sum to 100, not 110',
   'they sum to %s' % sum(w for _, w in got))
# The dates need room: 'dd/mm/yyyy' in Courier New 13px is about 78px of
# glyph, and the first cut of this round gave those columns 90px and the
# render came back reading '14/07/202' over '6'.
floors = dict((int(x.group(1)), int(x.group(2))) for x in re.finditer(
    r'\.task-list-table th:nth-child\((\d)\)[^{}]*\{[^}]*'
    r'min-width:\s*(\d+)px', c))
ok(floors.get(5, 0) >= 100 and floors.get(6, 0) >= 100,
   'and the two date columns have at least 100px of floor',
   'start %s, end %s' % (floors.get(5), floors.get(6)))

# ==========================================================================
head('7. THE EXCEL EXPORT SKIPS THE TWO ACTION CELLS')
# ==========================================================================
# The export reads cells out of the DOM. So does this - the page's own
# selector, run against the page's own row, counting what comes back.
j = js_of(now)
sel = re.search(r"const cells = row\.querySelectorAll\("
                r"\s*(.*?)\s*\);", j, re.S)
ok(sel is not None, 'the export still has a cell query')
if sel:
    q = sel.group(1)
    ok('th, td' != q.strip().strip("'\""),
       'and it is no longer the bare th, td that took every cell')
    ok('not(.cell-actions)' in q and 'not(.mobile-action-bar)' in q,
       'it excludes both the desktop cell and the phone bar')

if have_pw:
    from playwright.sync_api import sync_playwright
    fx = os.path.join(SCRATCH, 'fx_export.html')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><meta charset="utf-8">'
                 '<table class="task-list-table"><tbody>'
                 '<tr><td data-label="Name">Strip the tiles</td>'
                 '<td class="cell-type">TASK</td>'
                 '<td class="desktop-action-cell cell-actions">'
                 '<a>Edit</a><a>Delete</a></td>'
                 '<td class="mobile-action-bar cols-2">Edit Delete</td>'
                 '</tr></tbody></table>')
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 1280, 'height': 400})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        # The page writes the selector as two JS string literals joined
        # by +. Rebuild it the way the browser would, by taking the
        # quoted pieces and concatenating them - not by guessing at the
        # exact whitespace between them.
        query = ''.join(re.findall(r"'([^']*)'", sel.group(1))) if sel \
            else 'th, td'
        texts = pg.evaluate(
            "(q) => Array.from(document.querySelector('tr')"
            ".querySelectorAll(q)).map(c => c.textContent.trim())", query)
        print('       the page\'s own selector: %s' % query)
        br.close()
    ok(len(texts) == 2,
       'the row yields 2 data cells, not 4', 'it yielded %s' % texts)
    ok(not any('Delete' in t for t in texts),
       'and no column reading "Edit Delete" reaches the sheet',
       '%s' % texts)
else:
    skip('the export selector in a browser', 'playwright is not installed')

# ==========================================================================
head('8. THE CONTROL - PUT THE DRIFT BACK AND SECTION 3 MUST FAIL')
# ==========================================================================
# A check that cannot fail is not a check. This re-adds the page rule the
# round removed and asks the browser the same question again; the answer
# must change. It must FAIL, not crash.
if not have_pw:
    skip('the control', 'playwright is not installed')
else:
    DRIFT = ("""
@media screen and (max-width: 768px) {
    .task-list-table td[data-label]::before {
        content: attr(data-label);
        font-size: 11px;
        text-transform: uppercase;
        color: #6c757d;
    }
}
</style>""")
    hurt = now.replace('</style>', DRIFT, 1)
    ok(hurt != now, 'the control really did change the page')
    try:
        back = label_style(hurt, 'control')
        ok(back[0] != HOUSE[0] or back[1] != HOUSE[1],
           'with the drift back, the label is NOT the house label again',
           'it still measured %s' % (back,))
        print('       control measured %s' % (back,))
    except SystemExit:
        raise
    except Exception as e:
        ok(False, 'the control ran without crashing', e)

# ==========================================================================
head('9. THE GATE')
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
ok(os.path.isfile(PATH + SUFFIX),
   'the round left its backup beside the page')

print('')
print('  NOT THIS ROUND, and said rather than swept in: the row still')
print('  carries .task-type-project/-task/-subtask - a 4px left border')
print('  and a 3%% tint in #3498db / #2ecc71 / #f39c12. That is the same')
print('  category colour a fourth time, and removing it was not among the')
print('  seven questions Demetri answered. On a phone base\'s card rule')
print('  outranks it, so it does not fight the card.')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
