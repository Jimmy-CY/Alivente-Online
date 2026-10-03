# -*- coding: utf-8 -*-
"""SECTION AE, ROUND AE-1 AND AE-3 - ACTUAL EXPENSES

Two of the three Demetri raised on this screen. (AE-2, the tab colour,
is not here: the tree has no tab standard at all - base declares neither
.nav-link nor .nav-tabs, so 17 tabs across 5 templates are Bootstrap's
raw #007bff. That is a base component and its own round.)

    AE-1  "Fit Search, Property, Status, From and To on one line."
    AE-3  The drill-down Back: label to "Back", move it right, and hide
          the year selector while drilled down.

==========================================================================
AE-1 - AND THE DEFECT NOBODY REPORTED, WHICH WAS WORSE
==========================================================================
The five controls were not on one line because there were TWO GRIDS:

    .filter-grid       2fr 1fr 1fr     Search, Property, Status
    .date-filter-grid  150px 150px     From, To

The second one is why the dates sat on their own row. It is also wrong
in a way nobody could have reported, because the symptom looks like a
date:

    A DATE INPUT NEEDS 165px. Measured, in this sandbox's Chromium, by
    putting a date input with a real value at width:auto and reading its
    intrinsic width back: 165. That is 31/12/2026 plus the picker icon
    plus the component's own 14px padding and 2px border.

    .date-filter-grid gave it 150. At every desktop width, for as long as
    that rule has existed. And on the phone 162, from the 1fr 1fr it
    switched to at 768px.

So From and To have been clipping their own content, silently, at every
width. A truncated date still reads as a date, which is exactly why it
was never reported - and why it is measured here rather than eyeballed.

----------------------
ONE GRID, THREE BANDS
----------------------
.date-filter-grid is deleted and its two groups move into .filter-grid,
which then has five children and names the columns for each band. All
numbers below are measured at the panel widths Bootstrap's container
actually produces (1110 / 930 / 690 / 334 inner):

  >= 1200px   1.6fr 1.2fr 1.2fr 170px 170px   ONE LINE, which is AE-1
              Search 211  Property 192  Status 192  From 170  To 170

  769-1199    1fr 1fr 1fr                     three up, two under
              every control 200-280

  <= 768px    1fr                              stacked, 334 each

Every control clears 165 at every width. Five columns genuinely do not
fit below 1200: at a 690px panel the flexible tracks fall to 58px and
"All Properties" is unreadable. A band that cannot hold the line keeps
today's shape rather than pretending.

THE PHONE LOSES ITS SIDE-BY-SIDE DATES, AND THAT IS THE FIX. .date-filter-
grid put From and To 2-up at 162px each. Stacked they get 334. Every
other filter panel in the house stacks to 1fr on a phone - properties,
fsr, tenant, Receipts, Invoice Customers - so this also ends the one
page that did something else.

THE 1199px BAND SITS ABOVE THE 768px BLOCK IN THE FILE, deliberately.
Both match at 390px and the later rule wins, so the order is what makes
the phone rule hold. A gate below checks that order rather than trusting
it.

==========================================================================
AE-3 - THE DRILL-DOWN
==========================================================================
Three things, and the third is not cosmetic.

  THE LABEL said "Back to overview". Everything else in the house says
  "Back" - test_bar_top requires the word, test_body_backs listed this
  one as left alone because it is a drill-down return inside a page
  rather than a page Back. It still is; it just says Back now, and that
  suite's ledger is amended to say so.

  THE PLACE. It sat above the title, alone, at the left. It moves onto
  the title's line, at the right, which is where every Back in the house
  sits. The row it used to occupy is given back.

  THE YEARS BAR IS A TRAP WHILE DRILLED DOWN, not merely redundant.
  Every checkbox in it calls loadData(), and loadData() calls
  showOverview(). So touching a year while reading one property's
  expenses threw you out to the overview without saying why. It is
  hidden while the drill is open.

  AND THE HEADING CARRIES WHAT THE BAR WAS SAYING. Hiding the bar hides
  WHICH years the figures cover - the drill endpoint is passed the same
  year selection - so the heading becomes

      Athens - Second Floor - all years
      Athens - Second Floor - 2024, 2025

  built with textContent, like the name already was: a property called
  Smith & Co is a name, not markup.

Backups: .bak_aeline. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_aeline'
CRLF = {}
SENTINEL = 'test_ae_line.py'
ROOT = os.getcwd()

# The column template this round settles on, written once so the patcher,
# the gates and the suite cannot drift apart.
COLS = 'minmax(0, 1.6fr) minmax(0, 1.2fr) minmax(0, 1.2fr) 170px 170px'
MID = '1fr 1fr 1fr'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('AE: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in the file's own line endings, and refuse an
    anchor that lands mid-line.

    A3's lesson: an anchor beginning with spaces matches inside a MORE
    deeply indented line, so it edits real code at the wrong indentation
    and leaves a file that will not parse."""
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('AE: %s appears %d times, not once' % (what, c))
    i = text.index(o)
    if i and not o.startswith(('\n', '\r')) and text[i - 1] not in '\n\r':
        raise SystemExit('AE: the anchor for %s starts MID-LINE (after %r)'
                         % (what, text[i - 1]))
    return text.replace(o, n)


print('=' * 74)
print('SECTION AE - FIVE FILTERS ON ONE LINE, AND THE DRILL-DOWN%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

PAGE = alv_tree.join('act_expense.html')
pt, praw = read(PAGE)

print('')
print('  AE-1  THE FILTER ROW')
print('  ' + '-' * 70)

if 'minmax(0, 1.6fr)' in pt:
    print('  act_expense.html             already done')
else:
    # ----------------------------------------------------------------
    # the desktop rule, and the end of .date-filter-grid
    # ----------------------------------------------------------------
    pt = swap(pt, '''.filter-grid {
    grid-template-columns: 2fr 1fr 1fr;
    margin-bottom: 20px;
}

.date-filter-grid {
    display: grid;
    grid-template-columns: 150px 150px;
    gap: 20px;
    align-items: end;
}
''', '''/* FIVE FILTERS, ONE GRID - AE-1, 1 Oct 2026. Demetri: "Fit Search,
   Property, Status, From and To on one line."

   THEY WERE ON TWO LINES BECAUSE THEY WERE IN TWO GRIDS. This rule held
   the first three; a second rule, .date-filter-grid, held From and To at
   150px each and is deleted. Its two groups are children of this one
   now, so there are five.

   AND 150px WAS NEVER ENOUGH. A date input needs 165 - measured, not
   guessed: a date input carrying 31/12/2026 at width:auto reports 165px
   in Chromium, which is the text plus the picker icon plus this
   component's own 14px padding and 2px border. So From and To have been
   clipping their own value at every desktop width for as long as that
   rule existed, and at 162px on a phone. A truncated date still looks
   like a date, which is why nobody reported it. 170px leaves 5px.

   THREE BANDS, because five columns do not fit in every panel. Bootstrap
   caps the container, so the panel is 1110px wide on any screen from
   1200px up, 930 from 992, and 690 from 769. At 690 the flexible tracks
   would fall to 58px and "All Properties" would be unreadable - so that
   band keeps the shape it has today rather than pretending. Measured at
   each: every control clears 165 at every width.
                                                     [test_ae_line.py] */
.filter-grid {
    grid-template-columns: %s;
    margin-bottom: 20px;
}

/* THE BAND WHERE FIVE DO NOT FIT. Three up, two under - which is what
   the page looked like before AE-1, reached with one grid instead of
   two.

   THIS BLOCK MUST STAY ABOVE THE 768px BLOCK BELOW. A 390px phone
   matches both, and the later rule wins; if these two ever swap places
   the phone silently gets three columns at 100px each. There is a gate
   on the order in apply_ae_line.py and a check in the suite. */
@media screen and (max-width: 1199px) {
    .filter-grid {
        grid-template-columns: %s;
    }
}
''' % (COLS, MID), 'the desktop filter grid', PAGE)

    # ----------------------------------------------------------------
    # the mobile rule loses its date grid
    # ----------------------------------------------------------------
    pt = swap(pt, '''    .filter-grid {
        grid-template-columns: 1fr;
        gap: 12px;
        margin-bottom: 12px;
    }
    .date-filter-grid {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }
''', '''    /* ONE COLUMN, INCLUDING THE DATES - AE-1. There used to be a
       .date-filter-grid here putting From and To 2-up, which gave each
       of them 162px against the 165 a date input needs. Stacked they
       get 334, and this page stops being the only filter panel in the
       house that does not simply stack on a phone. */
    .filter-grid {
        grid-template-columns: 1fr;
        gap: 12px;
        margin-bottom: 12px;
    }
''', 'the mobile filter grid', PAGE)

    # ----------------------------------------------------------------
    # the markup: one grid, five children
    # ----------------------------------------------------------------
    pt = swap(pt, '''                    </select>
                </div>
            </div>

            <div class="date-filter-grid">
''', '''                    </select>
                </div>

''', 'the join between the two grids', PAGE)

    if not CHECK:
        back_up(PAGE, praw)
    print('  act_expense.html             2fr 1fr 1fr + 150px 150px -> %s'
          % COLS)
    print('  %-28s and 1fr 1fr 1fr from 769 to 1199, 1fr below' % '')

print('')
print('  AE-3  THE DRILL-DOWN')
print('  ' + '-' * 70)

if 'report-drill-head' in pt:
    print('  act_expense.html             already done')
else:
    # ----------------------------------------------------------------
    # the head: title left, Back right
    # ----------------------------------------------------------------
    pt = swap(pt, '''.report-drill-title { font-weight: 600; color: #2c3e50; margin-bottom: 12px; }
''', '''.report-drill-title { font-weight: 600; color: #2c3e50; margin-bottom: 12px; }
/* TITLE LEFT, BACK RIGHT - AE-3. The Back used to sit on its own line
   above the title, at the left, and said "Back to overview". It is on
   the title's line now, at the right, which is where every Back in the
   house sits, and it says Back. flex-shrink: 0 on the button so a long
   property name takes the squeeze instead of the word. */
.report-drill-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
}
.report-drill-head .report-drill-title { margin-bottom: 0; min-width: 0; }
.report-drill-head .btn { flex-shrink: 0; }
''', 'the drill-head rule', PAGE)

    pt = swap(pt, '''          <button type="button" class="btn action-back btn-sm mb-3" id="reportDrillBack">
            <i class="fas fa-arrow-left"></i> Back to overview
          </button>
          <h6 id="reportDrillTitle" class="report-drill-title"></h6>
''', '''          <div class="report-drill-head">
            <h6 id="reportDrillTitle" class="report-drill-title"></h6>
            <button type="button" class="btn action-back btn-sm" id="reportDrillBack">
              <i class="fas fa-arrow-left"></i> Back
            </button>
          </div>
''', 'the drill head markup', PAGE)

    # ----------------------------------------------------------------
    # the years bar, hidden while drilled down
    # ----------------------------------------------------------------
    pt = swap(pt, '''    function showOverview() {
        document.getElementById('reportDrill').style.display = 'none';
        document.getElementById('reportOverview').style.display = 'block';
    }
''', '''    // THE YEARS BAR IS A TRAP WHILE DRILLED DOWN, not just redundant.
    // Every checkbox in it calls loadData(), and loadData() ends by
    // calling showOverview() - so touching a year while reading one
    // property's expenses threw you back out to the overview, with
    // nothing on screen saying why. It is hidden while the drill is
    // open and restored with the overview. [AE-3]
    //
    // style.display = '' rather than 'flex': the stylesheet already says
    // flex, and a value written here would have to be kept in step with
    // it by hand.
    function yearBar(show) {
        var bar = document.querySelector('.report-year-bar');
        if (bar) { bar.style.display = show ? '' : 'none'; }
    }

    // WHAT THE HIDDEN BAR WAS SAYING, SAID IN THE HEADING INSTEAD. The
    // drill endpoint is passed the same year selection as the overview,
    // so with the bar gone there would be nothing on screen to say which
    // years these figures cover. [AE-3]
    function yearScope() {
        var p = selectedYearsParam();
        return p === 'all' ? 'all years' : p.split(',').join(', ');
    }

    function showOverview() {
        document.getElementById('reportDrill').style.display = 'none';
        document.getElementById('reportOverview').style.display = 'block';
        yearBar(true);
    }
''', 'showOverview', PAGE)

    pt = swap(pt, '''    function openDrill(propId, propName) {
        document.getElementById('reportDrillTitle').textContent = propName;
''', '''    function openDrill(propId, propName) {
        // textContent, not innerHTML - a property called Smith & Co is a
        // name, not markup. It was already textContent; the year scope
        // joins it on the same side of that line. [AE-3]
        document.getElementById('reportDrillTitle').textContent =
            propName + ' \\u00b7 ' + yearScope();
        yearBar(false);
''', 'openDrill', PAGE)

    if not CHECK:
        back_up(PAGE, praw)
        write(PAGE, pt)
    print('  act_expense.html             "Back to overview" -> "Back", '
          'moved right')
    print('  %-28s years bar hidden while drilled down; the' % '')
    print('  %-28s heading carries the year scope' % '')

# ==========================================================================
print('')
print('  THE TWO LEDGERS THAT KNEW THE OLD SHAPE')
print('  ' + '-' * 70)

# test_filter_frame.py reads apply_filter_frame.py's PANELS table for
# what each of nine pages KEEPS, and asserts the live file equals it.
# AE-1 moves act_expense's column template, so that claim has to move
# with it - but THE PATCHER IS HISTORY AND IS NOT EDITED. A patcher
# records what it did; the live ledger belongs to the suite. The
# amendment is declared in the suite, named, so the check stays exact
# rather than being loosened.
FF = os.path.join(ROOT, 'test_filter_frame.py')
ft, fraw = read(FF)
if 'AMENDED' in ft:
    print('  test_filter_frame.py         already done')
else:
    ft = swap(ft, '''base = read(alv_tree.path_of('base.html'))
''', '''# A LATER ROUND MAY MOVE A COLUMN TEMPLATE, AND ONE HAS.
#
# Section AE round AE-1, 1 Oct 2026, put Actual Expenses' five filters on
# one line, so its .filter-grid no longer says what apply_filter_frame.py
# recorded when H1 lifted the frame into base.
#
# THE PATCHER IS NOT EDITED TO MATCH. A patcher is the record of what it
# did on the day it ran; rewriting its tables to keep a later suite happy
# turns the record into a diary of the present. The live claim belongs
# here, which is also the file that asserts it. Amending it by name keeps
# the check EXACT - the alternative, loosening section 2 to compare key
# sets instead of values, would have stopped noticing a column template
# changing by accident, which is the thing it is for.
#                                                    [test_ae_line.py]
AMENDED = {
    ('act_expense.html', '.filter-grid', 'grid-template-columns'):
        ('2fr 1fr 1fr',
         'minmax(0, 1.6fr) minmax(0, 1.2fr) minmax(0, 1.2fr) 170px 170px'),
}

base = read(alv_tree.path_of('base.html'))
''', 'the AMENDED table', FF)

    ft = swap(ft, '''    want = dict((s, PANELS[rel][s]['keep']) for s in FRAME
                if PANELS[rel].get(s, {}).get('keep'))
''', '''    want = dict((s, dict(PANELS[rel][s]['keep'])) for s in FRAME
                if PANELS[rel].get(s, {}).get('keep'))
    for (a_rel, a_sel, a_key), (a_was, a_now) in AMENDED.items():
        if a_rel == rel and a_sel in want:
            if want[a_sel].get(a_key) != a_was:
                ok(False, '%s: AMENDED says %s used to be %r and the '
                   'patcher does not agree' % (rel, a_key, a_was),
                   want[a_sel].get(a_key))
            want[a_sel][a_key] = a_now
''', 'the want table', FF)

    # Section 3 renders each of the nine twice - from the backup and from
    # the live file - and fails if anything moved. act_expense's grid
    # columns moved, on purpose, and the exemption says exactly how much.
    ft = swap(ft, '''                if (k in ('header.mb', 'header.pb') and v[0] == '0px'
                        and rel in ('invoices.html', 'projects/projects.html')):
                    continue   # the two with no separator gain the house one
''', '''                if (k in ('header.mb', 'header.pb') and v[0] == '0px'
                        and rel in ('invoices.html', 'projects/projects.html')):
                    continue   # the two with no separator gain the house one
                if (k == 'grid.cols' and rel == 'act_expense.html'
                        and len(v[1].split()) == 5):
                    # AE-1 PUT FIVE FILTERS ON ONE LINE, 1 Oct 2026. The
                    # one thing this round is allowed to have moved since
                    # H1, and it is still a claim: FIVE tracks, measured
                    # in the browser, not merely "something changed".
                    continue
''', 'the grid.cols exemption', FF)

    if not CHECK:
        back_up(FF, fraw)
        write(FF, ft)
    print('  test_filter_frame.py         AE-1 amendment declared, by name')

# test_body_backs.py's LEFT_ALONE is printed, not asserted - but a
# printed ledger that is wrong is worse than no ledger, because it is
# read as fact and never checked.
BB = os.path.join(ROOT, 'test_body_backs.py')
bt, braw = read(BB)
if 'AE-3' in bt:
    print('  test_body_backs.py           already done')
else:
    bt = swap(bt, """    'act_expense \"Back to overview\"': 'a drill-down return within the page',
""", """    'act_expense drill Back': 'a drill-down return within the page - it '
                              'said \"Back to overview\" when this round '
                              'ran and says \"Back\" since AE-3, 1 Oct '
                              '2026; still not a page Back',
""", 'the LEFT_ALONE note', BB)
    if not CHECK:
        back_up(BB, braw)
        write(BB, bt)
    print('  test_body_backs.py           ledger says Back, not Back to '
          'overview')

# test_bar_top.py counts the Back controls tree-wide that still say
# something other than "Back". AE-3 fixed one of the three, so the count
# moves - and the sentence naming them has to move with it, or the suite
# goes on printing a list of three that contains two.
BT = os.path.join(ROOT, 'test_bar_top.py')
tt_, traw = read(BT)
if 'AE-3' in tt_:
    print('  test_bar_top.py              already done')
else:
    tt_ = swap(tt_, """    ('act_expense.html', 3):
        'a DRILL-DOWN return inside a report - it names where it goes '
        'because it goes somewhere on the same page',
""", """    ('act_expense.html', 3):
        'a DRILL-DOWN return inside a report, not a page Back. B2 left it '
        'saying "Back to overview"; AE-3 shortened it to "Back" on 1 Oct '
        '2026 and moved it onto the drill heading, at the right. It is '
        'still left alone BY THIS ROUND - the reason was never the label',
""", 'the LEFT reason', BT)

    tt_ = swap(tt_, """# Three, not four: project_task_list's label is a conditional, so it reads
# as no single word at all and never appears in this list.
ok(len(long_left) == 3,
   'three Back controls still say something else - Cancel, Back to '
   'overview, Go Back - and section 5 names each',
   long_left)
""", """# Three, not four: project_task_list's label is a conditional, so it reads
# as no single word at all and never appears in this list.
#
# AND TWO, NOT THREE, SINCE AE-3 (1 Oct 2026). The third was Actual
# Expenses' "Back to overview", which that round shortened to "Back" and
# moved onto the drill heading. B2 had left it alone because it is a
# drill-down return rather than a page Back, and it still is - what
# changed is that it now says the house word while being one.
#
# THE REMAINING TWO ARE NAMED, not counted. A bare number is what let the
# first version of this ledger go on listing three things after one of
# them had been fixed.
ok(sorted(long_left) == [('create_meal_plan.html', 'Cancel'),
                         ('error_pages/connectivity_error.html', 'Go Back')],
   'two Back controls still say something else - Cancel on a form, where '
   'Cancel may be right, and Go Back on an error page with no bar - and '
   'section 5 names each',
   long_left)
""", 'the long_left count', BT)

    if not CHECK:
        back_up(BT, traw)
        write(BT, tt_)
    print('  test_bar_top.py              three long Backs -> two, and both '
          'named')

# ==========================================================================
print('')
print('  REGISTRATION')
print('  ' + '-' * 70)
for rel, old, new, what in (
        ('alv_rounds.py', "    '.bak_importmodel',\n]\n",
         "    '.bak_importmodel',\n    '%s',\n]\n" % SUFFIX,
         'the end of ROUNDS'),
        ('Push-PendingChanges.ps1', "    'test_ai_models.py'\n)\n",
         "    'test_ai_models.py'\n"
         "    # Five filters on one line, and the drill-down. Its section\n"
         "    # 3 opens Chromium at six widths and reads back where every\n"
         "    # control landed, because the defect AE-1 fixes - a date\n"
         "    # input 15px narrower than a date - is invisible to a grep\n"
         "    # and was invisible on screen for as long as it existed.\n"
         "    'test_ae_line.py'\n)\n", 'the end of $suites')):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    if (SUFFIX if rel.endswith('.py') else SENTINEL) in tt:
        print('  %-34s already done' % rel)
        continue
    tt = swap(tt, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt)
    print('  %-34s registered' % rel)

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

import ast  # noqa: E402

for f in ('test_filter_frame.py', 'test_body_backs.py'):
    ast.parse(read(os.path.join(ROOT, f))[0])
print('  both amended suites parse')

now = read(PAGE)[0]


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


CODE = code_only(now)

# THE MARKUP STILL CLOSES. F2's lesson: an anchor that does not consume
# the closer it re-emits leaves the page one </div> heavier than it
# opened, and three suites said so AFTER the round had shipped.
body = re.sub(r'<(script|style)\b.*?</\1>', '',
              re.sub(r'<!--.*?-->|\{#.*?#\}', '', now, flags=re.S), flags=re.S)
n = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if n:
    raise SystemExit('AE: act_expense.html has %+d unbalanced <div>' % n)
print('  every <div> closes')

# .date-filter-grid IS GONE FROM BOTH SIDES - rule and markup. A class
# left in the CSS with nothing wearing it is the next reader's puzzle.
if 'date-filter-grid' in CODE:
    raise SystemExit('AE: .date-filter-grid is still named in the page')
print('  .date-filter-grid is gone from the stylesheet and the markup')
print('    (the notes still name it, which is what a note is for - the')
print('     gate reads code_only(), not prose)')

# FIVE CHILDREN IN ONE GRID.
m = re.search(r'<div class="filter-grid">(.*?)\n            </div>', CODE,
              re.S)
if not m:
    raise SystemExit('AE: the filter grid could not be found')
kids = len(re.findall(r'<div class="filter-group">', m.group(1)))
if kids != 5:
    raise SystemExit('AE: the filter grid has %d children, not 5' % kids)
print('  the one grid has five .filter-group children')

# AND THE BANDS ARE IN THE RIGHT ORDER. 390px matches both media blocks
# and the later one wins, so this is the rule that makes the phone rule
# hold. Stated as a gate rather than left to whoever edits next.
i_mid = CODE.find('max-width: 1199px')
i_small = CODE.find('max-width: 768px')
if not (0 < i_mid < i_small):
    raise SystemExit('AE: the 1199px block is not above the 768px block - '
                     'the phone would get three columns')
print('  the 1199px band sits above the 768px band, so the phone wins')

# NO LITERAL COLOUR ENTERED THE PAGE.
was = read(PAGE + SUFFIX)[0]
f_now = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', now))
f_was = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', was))
if f_now > f_was:
    raise SystemExit('AE: the page gained %d literal colour(s)'
                     % (f_now - f_was))
print('  literal colours %d -> %d' % (f_was, f_now))

# EVERY action-back ON THE PAGE SAYS "Back".
bad = [m for m in re.findall(r'<(?:a|button)[^>]*\baction-back\b.*?</(?:a|button)>',
                             CODE, re.S)
       if not re.search(r'>\s*Back\s*<|>\s*Back\s*$|Back</span>', m)]
if bad:
    raise SystemExit('AE: an action-back does not say Back:\n%s' % bad[0][:200])
print('  every action-back on the page says Back')

print('-' * 74)
print('  Search, Property, Status, From and To sit on one line, and each of')
print('  them is wide enough to show what it holds. The drill-down says Back,')
print('  on the right, and the years bar no longer throws you out of it.')
print('=' * 74)
