# -*- coding: utf-8 -*-
"""test_pl_invoice_col.py - Section PL round PL-1, 5 Oct 2026.

Demetri, of Dashboard -> Profit & Loss: "to view a copy of a specific
invoice I need to click the little black tick. This is not intuitive."

The tick is verify_badge - a STATUS glyph that draws fa-check-circle,
fa-exclamation-triangle, fa-question-circle, fa-file or fa-object-group
depending on whether the invoice was verified. It was also the only way
to open the document. Nothing about a tick says DOCUMENT.

PL-1 adds an Invoice column to the drill-down branch of
act_expense.html - the branch the modal scrapes - carrying the same
.report-invoice-icon the full page already uses in its Actions column,
and a dash where there is no document.

WHAT THIS SUITE CANNOT DO, said plainly because the gap is real: the
modal builds itself by fetching act_expense.html over AJAX and lifting
`table.table` out of the response. Nothing here can run that fetch. So
section 3 renders THE TABLE - the exact thing that gets scraped - in
both branches, and checks the column is present, in the right place,
with a control in it. Whether the modal then displays it is Demetri's to
confirm on Live, and this suite says so rather than implying otherwise.

NOTHING WAS TAKEN AWAY, and section 4 is the guard on that. The tick
still carries its status and still opens the document. The complaint was
that the only way in was unfindable, not that the tick was wrong - so
the round adds the obvious control rather than moving the hidden one. A
later round that decides to make the badge status-only should have to
change this suite deliberately.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree

try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_plinvcol'
ME = 'test_pl_invoice_col.py'
PATCHER = 'apply_pl_invoice_col.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = alv_tree.path_of('act_expense.html')
PL = alv_tree.path_of('finance_pl_act.html')
BOOTF = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


SRC, OLD = now(PAGE), was(PAGE)


TABLE_RE = re.compile(r'<table[^>]*expense-table[^>]*>[\s\S]*?</table>')


def table_of(text):
    """Just the expense table. The page is 122 KB and reads the flag in a
    dozen places, several of them inside <script>; resolving it over the
    whole file matched an {% endif %} belonging to someone else and the
    first build of this suite failed on a round that was correct."""
    m = TABLE_RE.search(text)
    return m.group(0) if m else ''


IF_POS = re.compile(r'\{%\s*if from_finance_pl_act\s*%\}')
IF_NEG = re.compile(r'\{%\s*if not from_finance_pl_act\s*%\}')
ANY_IF = re.compile(r'\{%\s*if\b[^%]*%\}')
ANY_END = re.compile(r'\{%\s*endif\s*%\}')


def branch(text, drill):
    """The table as it renders for one value of the flag.

    NESTING-AWARE, because a non-greedy regex pairs an {% if %} with the
    FIRST {% endif %} it meets, and these blocks contain others. Walks
    forward counting depth, exactly as a template engine would."""
    text = table_of(text)
    while True:
        m = IF_NEG.search(text) or IF_POS.search(text)
        if not m:
            return text
        want = bool(IF_POS.match(m.group(0))) == drill
        depth = 1
        i = m.end()
        while depth and i < len(text):
            nxt_if = ANY_IF.search(text, i)
            nxt_end = ANY_END.search(text, i)
            if not nxt_end:
                return text          # unbalanced; leave it alone
            if nxt_if and nxt_if.start() < nxt_end.start():
                depth += 1
                i = nxt_if.end()
            else:
                depth -= 1
                i = nxt_end.end()
                if not depth:
                    inner = text[m.end():nxt_end.start()]
                    text = text[:m.start()] + (inner if want else '') \
                        + text[i:]
    # unreachable


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the tick really was the only way in')

old_drill = branch(OLD, True)
ok('verify-icon' in old_drill,
   'the drill-down carried the verify badge',
   'it did not - then the finding is about another control')
ok('report-invoice-icon' not in old_drill,
   '  and no document control of its own',
   'it had one - then this round is solving a problem that was solved')
# THE PATTERN COMES FROM THE SCREEN DEMETRI NAMED, not from this page.
# My first draft asserted that act_expense's own full-page table already
# had a document control in its Actions column. It does not - this page
# has no such control anywhere in its table, which is a smaller finding
# of its own. The shape being copied is property_detail.html's Actual
# Expenses table: `<td data-label="Invoice">`, a fa-file-alt, and a dash
# where there is none. That is the screen he said was more intuitive.
PATTERN = read(alv_tree.path_of('property_detail.html'))
ok('data-label="Invoice"' in PATTERN and 'fa-file-alt' in PATTERN,
   '  while the Actual Expenses screen he preferred already had one',
   'property_detail.html has no Invoice column - then the pattern this '
   'round copies does not exist')

# ==========================================================================
head('2. and now it has a column that says so')

drill = branch(SRC, True)
full = branch(SRC, False)

ok('>Invoice</th>' in drill, 'the drill-down has an Invoice column header')
ok('report-invoice-icon' in drill, '  with the house document control in it')
ok('report-invoice-none' in drill,
   '  and a dash where there is no document, rather than an empty cell')
ok('title="View invoice"' in drill and 'aria-label="View invoice"' in drill,
   '  named, so it reads as a document and not as decoration')

# THE FULL PAGE IS UNTOUCHED. Both edits sit inside the drill-down
# branch; the Actions column it already had is not this round's.
ok('>Invoice</th>' not in full,
   'and the full Actual Expenses page gained no column',
   'it did - then the round reached outside the branch it claims')
# WHITESPACE-NORMALISED, because branch() leaves a blank line where it
# removes a block and that is an artefact of this suite, not of the
# round. Comparing raw bytes failed on two empty lines.
def squeeze(x):
    return re.sub(r'\s+', ' ', x).strip()


ok(squeeze(full) == squeeze(branch(OLD, False)),
   '  not a character of its table moved',
   'it changed - the diff is the round reaching where it said it would '
   'not')

# ==========================================================================
head('3. the table that gets scraped, rendered')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def detag(s):
    s = re.sub(r'\{%\s*(block|endblock|extends|load|csrf_token)[^%]*%\}', '', s)
    s = re.sub(r'\{%\s*(else|endif|endfor|empty)\s*%\}', '', s)
    s = re.sub(r'\{%[^%]*%\}', '', s)
    s = re.sub(r'\{\{[^}]*\}\}', 'Sample', s)
    return re.sub(r'\{#.*?#\}', '', s, flags=re.S)


FA = ('i[class*="fa-"]{display:inline-block;width:1em;height:1em;'
      'vertical-align:-0.125em;background:#8a979d;}')
BASECSS = css_of(alv_tree.code_only(now(alv_tree.path_of('base.html'))))

TABLE = """() => {
  const t = document.querySelector('table.expense-table');
  if (!t) return {none: 1};
  const heads = [...t.querySelectorAll('thead th')].map(h =>
      h.textContent.trim().replace(/\\s+/g, ' '));
  const cells = [...t.querySelectorAll('tbody tr')].slice(0, 1)
      .map(r => [...r.children].map(c => c.className || '-'));
  return {heads, cells, icons: t.querySelectorAll('.report-invoice-icon').length};
}"""

if sync_playwright is None:
    print('  --    the render  (playwright missing)')
else:
    exe = '/opt/pw-browsers/chromium'
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        for label, raw in (('drill-down', drill), ('full page', full)):
            body = re.sub(r'<script[^>]*>.*?</script>', '', raw,
                          flags=re.S | re.I)
            page = ('<!doctype html><html><head><meta charset="utf-8">'
                    '<style>%s</style><style>%s</style><style>%s</style>'
                    '</head><body>%s</body></html>'
                    % (read(BOOTF), BASECSS, FA, detag(body)))
            pg = br.new_page(viewport={'width': 1180, 'height': 900})
            pg.set_content(page)
            pg.wait_for_timeout(260)
            r = pg.evaluate(TABLE)
            pg.close()
            if r.get('none'):
                ok(False, '%s: the table rendered' % label)
                continue
            print('      %-11s headers: %s' % (label, ' | '.join(r['heads'])))
            if label == 'drill-down':
                ok('Invoice' in r['heads'],
                   '  the drill-down table really draws an Invoice header',
                   r['heads'])
                ok(r['heads'].index('Invoice') == len(r['heads']) - 1,
                   '  as its last column, where the eye looks for an action',
                   r['heads'])
                ok(len(r['cells'][0]) == len(r['heads']) if r['cells'] else
                   False,
                   '  and the row has exactly as many cells as headers',
                   'a header with no cell shifts every column one left')
            else:
                ok('Invoice' not in r['heads'],
                   '  the full page draws no Invoice header', r['heads'])
        br.close()

# ==========================================================================
head('4. and the tick still works')

ok('verify-icon' in drill,
   'the verify badge is still there - it is a real status',
   'it was removed; this round claims it was not')
m = re.search(r'<i[^>]*verify-icon[^>]*>', drill)
ok(m is not None and 'data-invoice-url' in m.group(0),
   '  and still carries the url, so pressing it still opens the document',
   'the badge lost its url - that is a removal, and this round adds')
# THIS IS THE CHECK THAT EARNED ITS KEEP. The drill-down's handler
# listened for .verify-icon and nothing else, so the new column's icon
# would have been a document button that did nothing when pressed -
# worse than the unfindable tick, which at least worked. PL-1 widens
# the delegate; this requires it.
handler = now(PL)
ok(handler.count(".on('click', '.verify-icon, .report-invoice-icon'") == 1,
   '  and the drill-down handler now listens for BOTH',
   'finance_pl_act.html does not delegate to .report-invoice-icon - then '
   'the new column opens nothing')
ok(was(PL).count(".on('click', '.verify-icon'") == 1,
   '  CONTROL: before this round it listened for the tick alone',
   'it already listened for both - then there was nothing to widen')

# ==========================================================================
head('5. the control - a header with no cell')

planted = SRC.replace('<td data-label="Invoice" class="cell-invoice">',
                      '<td data-label="Invoice" class="cell-invoice-X">', 1)
ok(planted != SRC, 'the control could be planted')
d2 = branch(planted, True)
ok('class="cell-invoice"' not in d2,
   '  and the check can tell the cell apart from its header',
   'it cannot - then section 3 would pass a table with a column missing')
ok('class="cell-invoice"' in drill, '  and the page itself is intact')

# ==========================================================================
head('6. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is in the push suites' % ME)

# ==========================================================================
print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that the MODAL shows the column. It builds')
print('  itself from an AJAX fetch of this page and lifts table.table out')
print('  of the response; nothing in this sandbox can run that fetch.')
print('  What is proved is that the scraped table carries the column.')
