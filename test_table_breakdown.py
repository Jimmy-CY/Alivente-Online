# -*- coding: utf-8 -*-
"""test_table_breakdown.py - Section H round H5b, 28 Sep 2026.

The last of the twelve Personal tables, and the only one that was keeping
TWO complete renderings of the same numbers: a table above 768px, and a
list of .breakdown-card divs built by 3.6KB of JavaScript below it.
.alv-table is that second renderer, in base, for every table in the
application - so the round deleted one rather than adding one.

SECTION 3 IS THE ONE THAT MATTERS, because deleting a renderer is the
easiest way to lose something quietly. It checks every name the cards
used is gone, AND - field by field - that what the card was showing is
still built by the row: the amount line and the not-mapped badge were
always interpolated into td.bt-name as well, so the only thing the cards
held alone was their labels, and data-label is where those go.

SECTION 4 IS RENDERED, and it borrows its fixture from render_h5b.py
rather than building a second one, because this table has nothing in it:
every row is built by a script from data the server sends to a dialog. An
ordinary fixture shows an empty table inside a closed modal - and
.modal.fade is opacity 0 as well as display none, which is why forcing
only the display produces four white pictures.
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


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_tablebreakdown'
ME = 'test_table_breakdown.py'
PATCHER = 'apply_table_breakdown.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
REL = 'view_recipe.html'
PAGE = os.path.join(T, REL)

# The five columns and the label each cell shows on a phone. Read off the
# table's own <th> text, which is the only place they were ever written
# down: this page never collapsed its table, so it never had the
# nth-child ::before rules the other Personal tables kept their labels in.
COLS = ['Ingredient', 'Calories', 'Carbs (g)', 'Fat (g)', 'Protein (g)']

# EVERY NAME THE SECOND RENDERER USED. If one comes back, so has it.
CARD_NAMES = [
    'breakdownCardsWrap', 'breakdown-cards-wrap', 'breakdown-card',
    'breakdown-card-header', 'breakdown-card-name', 'breakdown-card-amount',
    'breakdown-card-status', 'breakdown-card-row', 'breakdown-card-label',
    'breakdown-card-value',
]

# What the card was showing, and where the same thing lives in the row.
# Checked BEFORE the cards were deleted, and checked here so it stays true.
CARRIED = {
    'the ingredient name': ('breakdown-card-name', 'bt-name'),
    'the amount line': ('breakdown-card-amount', 'bt-amount'),
    'the not-mapped badge': ('breakdown-card-status', 'bt-status'),
}

# Page logic: what this page knows about its own data and base does not.
KEEP = [
    '.breakdown-table tbody td.bt-name',
    '.breakdown-table tbody td.bt-name .bt-amount',
    '.breakdown-table .bt-na',
]

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
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def css_of(t):
    """Style bodies with CSS COMMENTS STRIPPED. Both of this round's own
    self-checks first counted a brace and a class name that appeared only
    inside the note explaining them - a comment is not code, in this
    direction too (lesson 21)."""
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)), flags=re.S)


def markup_no_comments(t):
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def css_of(t):
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)),
                  flags=re.S)


def markup(t):
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def js_of(t):
    return '\n'.join(SCRIPT.findall(
        re.sub(r'<!--.*?-->', ' ', t, flags=re.S)))


ROW = re.compile(r'<tr[^>]*>\s*(?:<td[^>]*>.*?</td>\s*){5}</tr>', re.S)


def js_rows(t):
    """The two five-cell row templates the script builds: the body row and
    the totals row."""
    return [[c.group(0) for c in re.finditer(r'<td\b[^>]*>', m.group(0))]
            for m in ROW.finditer(js_of(t))]


def labels(tags):
    out = []
    for x in tags:
        m = re.search(r'data-label="([^"]*)"', x)
        out.append(m.group(1) if m else None)
    return out


def sel_here(css, want):
    w = ' '.join(want.split())
    return sum(1 for m in RULE.finditer(css)
               if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                  flags=re.S).split()) == w)


t_now, t_was = now(PAGE), was(PAGE)

# ==========================================================================
head('1. THE TABLE WEARS THE HOUSE COMPONENT')
# ==========================================================================
mk = markup(t_now)
m = re.search(r'<table[^>]*class="([^"]*)"[^>]*>', mk)
names = re.search(r'<table[^>]*class="([^"]*breakdown-table[^"]*)"',
                  mk).group(1).split()
ok(names[:2] == ['table', 'alv-table'],
   'the table reads `table alv-table breakdown-table`', ' '.join(names))
i = mk.find('breakdown-table')
ok('table-container' in mk[max(0, i - 260):i],
   '  and sits in a .table-container')
ok('breakdown-table-wrap' not in t_now,
   '  the old wrapper is GONE, not nested inside the new one - '
   '.table-container sets overflow:clip and the wrapper set overflow-x:'
   'auto, and a scroll container swallows a sticky heading',
   t_now.count('breakdown-table-wrap'))
ok('breakdown-table-wrap' in t_was,
   '  CONTROL: the backup had it')
ok(len(re.findall(r'<th class="bt-num num">', mk)) == 4,
   '  the four numeric headings wear base\'s .num beside their own class',
   len(re.findall(r'<th class="bt-num num">', mk)))

# ==========================================================================
head('2. BOTH JS ROW TEMPLATES CARRY THEIR LABELS')
# ==========================================================================
rows_now = js_rows(t_now)
ok(len(rows_now) == 2,
   'the script still builds exactly two five-cell rows - a body row and '
   'the totals', len(rows_now))
if len(rows_now) == 2:
    body_row, foot_row = rows_now
    ok(labels(body_row) == COLS,
       '  the body row is labelled %s' % ', '.join(COLS), labels(body_row))
    # THE TOTALS ROW'S FIRST CELL IS DELIBERATELY UNLABELLED.
    ok(labels(foot_row) == [None] + COLS[1:],
       '  the totals row carries the four figures\' labels and NOT '
       '"Ingredient" - that line reads "Per 100g total", and labelling it '
       'would make the phone card say "Ingredient: Per 100g total"',
       labels(foot_row))
    nums = [x for x in body_row[1:]]
    ok(all(' num' in x or '"num' in x for x in nums),
       '  every figure cell wears base\'s .num', nums)
rows_was = js_rows(t_was)
ok(rows_was and all(x is None for x in labels(rows_was[0])),
   'CONTROL: the backup\'s rows had no data-label at all',
   labels(rows_was[0]) if rows_was else 'no rows found')

# ==========================================================================
head('3. THE SECOND RENDERER IS GONE, AND NOTHING WENT WITH IT')
# ==========================================================================
for name in CARD_NAMES:
    ok(name not in t_now, 'no trace of %s' % name, t_now.count(name))
ok(all(n in t_was for n in CARD_NAMES),
   '  CONTROL: the backup used every one of those names')

# The card was not showing anything the row does not - checked field by
# field, and checked HERE so it stays true.
js_now = js_of(t_now)
js_was = js_of(t_was)
for what, (card_cls, row_cls) in sorted(CARRIED.items()):
    ok(card_cls in js_was,
       '%-22s the card had .%s' % (what, card_cls))
    ok(row_cls in js_now,
       '  %-20s and the ROW still builds .%s, so it was never the '
       'card\'s alone' % ('', row_cls), row_cls in js_now)

ok(len(js_was) - len(js_now) > 3000,
   '%d characters of JavaScript removed'
   % (len(js_was) - len(js_now)),
   '%d -> %d' % (len(js_was), len(js_now)))
ok('function renderBreakdown' in js_now,
   '  and the function that draws the table is still there - this round '
   'deleted a renderer, not the renderer')
ok(js_now.count('cardsHtml') == 0 and js_was.count('cardsHtml') > 0,
   '  cardsHtml is gone, and the backup had it',
   '%d now, %d before' % (js_now.count('cardsHtml'),
                          js_was.count('cardsHtml')))

# ==========================================================================
head('4. RENDERED - THE TABLE IS THE PHONE LAYOUT NOW')
# ==========================================================================
# The whole point of the round: BEFORE, the table was display:none below
# 768px and a hand-built card list stood in its place. AFTER, the table
# IS the card list. Both facts are geometry, so both are measured.
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('section 4', 'playwright unavailable: %s' % str(_e)[:40])

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 4', 'playwright or the bootstrap fixture is gone')
else:
    sys.path.insert(0, ROOT)
    try:
        import importlib.util as _il
        _sp = _il.spec_from_file_location('_r5b',
                                          os.path.join(ROOT,
                                                       'render_h5b.py'))
        _R = _il.module_from_spec(_sp)
        _sp.loader.exec_module(_R)
    except Exception as _e:
        _R = None
        skip('section 4', 'render_h5b.py would not load: %s' % str(_e)[:50])

    if _R is not None:
        PROBE = """() => {
            const t = document.querySelector('.breakdown-table');
            if (!t) return null;
            const b = t.getBoundingClientRect();
            const r = t.querySelector('tbody tr');
            const f = t.querySelector('tfoot tr');
            const cs = e => getComputedStyle(e);
            // TWO ARGUMENTS. `cs` takes one, so cs(e, '::before') asked
            // the ELEMENT for its content and every prefix came back
            // "normal" - three checks red against a page that was right.
            const pre = e => getComputedStyle(e, '::before').content;
            return {
                tableW: Math.round(b.width),
                rowH: r ? Math.round(r.getBoundingClientRect().height) : -1,
                footBg: f ? cs(f.querySelector('td')).backgroundColor : null,
                footInk: f ? cs(f.querySelector('td')).color : null,
                prefixes: r ? [...r.children].map(c => pre(c)) : [],
                // NOT text-align. base lays a phone cell out as a flex
                // row, so the figure is pushed right by justify-content
                // and its text-align is irrelevant - it reads 'left' on a
                // cell whose number is hard against the right edge. What
                // is true at both widths is that the figure ends where
                // the cell ends, so measure THAT.
                nums: r ? [...r.children].slice(1).map(c => {
                    const cb = c.getBoundingClientRect();
                    const rg = document.createRange();
                    rg.selectNodeContents(c);
                    const tb = rg.getBoundingClientRect();
                    return Math.round(cb.right - tb.right);
                }) : [],
                deskAlign: r ? [...r.children].slice(1)
                               .map(c => cs(c).textAlign) : []
            };
        }"""
        with sync_playwright() as pw:
            try:
                br = pw.chromium.launch(**({'executable_path': EXE}
                                           if os.path.exists(EXE) else {}))
            except Exception as _e:
                br = None
                skip('section 4', 'no browser: %s' % str(_e)[:40])
            if br is not None:
                def look(text, labelled, w):
                    fp = os.path.join(SCRATCH, 'fx.html')
                    with open(fp, 'w', encoding='utf-8') as fh:
                        fh.write(_R.fixture(text, labelled))
                    pg = br.new_page(viewport={'width': w, 'height': 2200})
                    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
                    _goto(pg, fp)
                    out = pg.evaluate(PROBE)
                    pg.close()
                    return out

                b390 = look(t_was, False, 390)
                a390 = look(t_now, True, 390)
                ok(b390 and b390['tableW'] == 0,
                   'CONTROL: before this round the table was invisible at '
                   '390px - a separate card list stood there', b390)
                ok(a390 and a390['tableW'] > 0,
                   'after: the table IS the phone layout', a390)
                ok(a390 and a390['prefixes'][1:] ==
                   ['"%s"' % c for c in COLS[1:]],
                   '  and each figure is prefixed with its heading, which '
                   'is what the card\'s label column was doing',
                   a390['prefixes'] if a390 else None)
                ok(a390 and a390['prefixes'][0] == 'none',
                   '  while the ingredient name is the card TITLE and '
                   'takes no prefix', a390['prefixes'][0] if a390 else None)
                ok(a390 and all(g <= 2 for g in a390['nums']),
                   '  and every figure is hard against the right edge of '
                   'its cell on a phone, which is what the card\'s value '
                   'column did', a390['nums'] if a390 else None)

                b12 = look(t_was, False, 1280)
                a12 = look(t_now, True, 1280)
                ok(b12 and b12['footBg'] == 'rgb(40, 167, 69)',
                   'CONTROL: the totals bar was Bootstrap green #28a745',
                   b12['footBg'] if b12 else None)
                ok(a12 and a12['footBg'] != 'rgb(40, 167, 69)',
                   '  and it is the house surface now',
                   a12['footBg'] if a12 else None)
                ok(a12 and a12['tableW'] > 800,
                   '  the desktop table is still a table', a12['tableW'])
                ok(a12 and set(a12['deskAlign']) == {'right'},
                   '  and base\'s .num right-aligns the figures there the '
                   'ordinary way', a12['deskAlign'] if a12 else None)
                br.close()

# ==========================================================================
head('5. THE CSS base NOW OWNS IS GONE, AND PAGE LOGIC IS NOT')
# ==========================================================================
cn, cw = css_of(t_now), css_of(t_was)


def breakdown_rules(css):
    return sum(1 for m in RULE.finditer(css)
               if 'breakdown' in ' '.join(m.group(1).split()))


ok(breakdown_rules(cw) - breakdown_rules(cn) == 26,
   '26 rule(s) deleted  (%d -> %d)'
   % (breakdown_rules(cw), breakdown_rules(cn)),
   'got %d' % (breakdown_rules(cw) - breakdown_rules(cn)))
ok(not any('breakdown-card' in ' '.join(m.group(1).split())
           for m in RULE.finditer(cn)),
   '  and not one .breakdown-card rule is left')
for sel in KEEP:
    ok(sel_here(cn, sel) == 1, '  %s is kept' % sel[:58])
ok(breakdown_rules(cn) >= 3,
   '  %d rule(s) kept - the amount line, the N/A italics and the '
   'not-mapped state are what this page knows about its own data'
   % breakdown_rules(cn))

# ==========================================================================
head('6. CONTROLS, AND THE GATE')
# ==========================================================================
ok(css_of('<style>a{/* } */ color: red}</style>').count('}') == 1,
   'the CSS reader ignores a brace inside a comment (lesson 21)')
ok('breakdown-card' not in markup(
    '<script>var a = "breakdown-card";</script>'),
   '  and the markup reader does not see a name used only in a script')
ok('breakdown-card' in js_of('<script>var a = "breakdown-card";</script>'),
   '  while the script reader does - which is how section 3 can say the '
   'renderer is gone rather than merely hidden')

ok('alv-table' not in markup(t_was),
   'reverting takes .alv-table off the table, so section 1 would FAIL - '
   'a revert is caught')
ok(any(n in t_was for n in CARD_NAMES),
   '  and brings the second renderer back, so section 3 would FAIL too')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and '.bak_tablepreview' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_tablepreview'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)
ok(os.path.isfile(os.path.join(ROOT, 'render_h5b.py')),
   '  and the sheet that section 4 borrows its fixture from is here too')

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the breakdown belongs inside a modal at')
print('  all. It is now one table instead of two renderings of one, and')
print('  the dialog it lives in is unchanged.')
print('=' * 74)
sys.exit(1 if failed else 0)
