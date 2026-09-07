"""apply_ia_drill.py - C3: the drill-down's table joins the standard, and the
   Issues module is finished.

    python apply_ia_drill.py --check     dry run, writes nothing
    python apply_ia_drill.py

Run from the repo root. Closes section 2.B - the fifth and last Issues screen.

THE FIFTH HAND-ROLLED TABLE, AND THE LAST ONE IN THIS MODULE.

`table.ia-tbl` is TWELVE rules - seven for the desktop table and five more
rebuilding it as phone cards: thead hidden, cells set to display:block, a
`data-label` prefix injected by ::before. With `.ia-empty-row` that is
THIRTEEN deleted, of which TWO come back rescoped (the issue link and its
hover), so ELEVEN are net gone - every one of them something base's
.alv-table already does, and does the same way.

THE ARITHMETIC IS SPELLED OUT BECAUSE THE FIRST DRAFT GOT IT WRONG, and in
the same way as two other slips this week: it counted the STRING
`table.ia-tbl` (16 occurrences, one of them inside a comment and four of them
inside a single grouped selector) and called the answer "rules". Characters
counted as bytes, samples counted as bands, and now occurrences counted as
rules. The unit is the part worth checking.

THE MARKUP WAS ALREADY SHAPED FOR IT, which is what makes this round mostly a
deletion. drillRows() already writes `data-label` on every cell and
`class="num"` on the figures - base's own conventions, arrived at
independently. The table did not need rebuilding; it needed renaming.

WHAT WAS MEASURED RATHER THAN ASSUMED, because three of these would have been
wrong if argued.

  1. THE STICKY HEADING STILL WORKS. This was the round's open question: base
     drives its heading shadow from an IntersectionObserver that runs ONCE at
     page load, over `.alv-table thead`, with the VIEWPORT as its root. This
     table is built by drillRows() long after load and scrolls inside the
     dialog, not the page, so that observer can never see it.

     But the STICKINESS itself is plain CSS - `position: sticky; top: 0` on
     .alv-table thead th - and it pins against the nearest scrolling
     ancestor, which is .ia-drill-body. Rendered and measured: the heading's
     top sits exactly on the drill body's top after scrolling. Nothing to fix.

  2. ONLY THE SHADOW IS MISSING, AND IT IS NOT WORTH BUYING. base's `.is-stuck`
     cue adds a soft shadow under the pinned heading - a hint that the row is
     floating over the list rather than sitting at the top of it. Rendered
     side by side, on and off, the difference is one faint shadow. The dialog
     already has a hard edge, a title bar and a drop shadow of its own, so the
     hint has almost nothing to do here. Left out DELIBERATELY. Written down
     so the next reader does not re-investigate it, and so it is not mistaken
     for base's table being broken inside a dialog.

  3. THE .table-container WRAPPER IS OMITTED. base's tables usually sit in
     one, but it exists to give a page card its background, radius and
     shadow, and to be the hook `.is-stuck` toggles. The dialog already
     provides the card and clips the wrapper's radius away; the hook is the
     cue we just declined. Rendered both ways: pixel-identical, and sticky
     pins in both. So the simpler markup wins, on evidence rather than taste.

AND ONE THING THE FIRST RENDER CAUGHT THAT WOULD HAVE SHIPPED BROKEN.
`table.ia-tbl a.ia-link` is scoped to the OLD class name. Rename the table
and that rule stops matching, and every issue link in the drill-down falls
back to Bootstrap's blue - which is exactly what the first render showed. The
rule is rescoped to `.ia-drill-body .alv-table a.ia-link`. A rename is not a
rename when other selectors are anchored to the old name.

THE OVERLAY ITSELF STAYS HAND-ROLLED, and that is a decision rather than an
omission. base has NO modal component - the system uses Bootstrap modals, and
this is a dialog inside one at z-index 2000, which Bootstrap does not do.
One asker; base has twice declined to build on one, most recently on 2 Sep
when a compact stat density was proposed, approved, built and then dropped
after measuring. Round C1 already tokenised these rules, so the overlay
spells no colour by hand - it is only its SHAPE that is still local.

DENSITY: BASE'S TABLE AS IT IS. Base's rows are 71px against ia-tbl's 59px,
so the dialog shows three at a time instead of four. Considered and taken:
the drill-down is a list you scan and scroll, not a page you read, and a
compact variant in base would be its SECOND asker (tenant_payment_days
hand-rolls `.pd-table-compact tbody td { padding: 8px 12px }` against base's
11px 12px). Section 1.F stays open for a round with more askers than two.

HOUSE RULES: idempotent, .bak_iadrill backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
IA = os.path.join(T, 'fsr.html')
BASE = os.path.join(T, 'base.html')
for _p in (IA, BASE):
    if not os.path.exists(_p):
        sys.exit('! %s not found - run from the repo root' % _p)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:120]))
    return t.replace(old, new, 1)


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


F_ORIG, F_CRLF, f = load(IA)
# THE MARKER READS THE CODE, NOT THE FILE - twenty-third time a check that
# reads text has caught prose, and the first time it has been the IDEMPOTENCE
# marker, which is the worst place for it. The first draft said
# `'ia-tbl' not in f`, and the note this round adds QUOTES the old selector
# while explaining why it was rescoped. So the marker never fired, and a
# second run walked straight into its own anchor.
#
# Two halves, both needed. A one-line phrase from the note - it must not wrap,
# or it can never match - and the code test on comment-stripped text.
_f_nc = re.sub(r'/\*.*?\*/', '', f, flags=re.S)
DONE = ("THE DRILL TABLE IS BASE'S NOW" in f) and ('ia-tbl' not in _f_nc)
if DONE:
    print('  fsr.html already patched')
else:
    # =======================================================================
    # 1. the desktop rules - seven go, two of them come back rescoped
    # =======================================================================
    # Every deleted declaration has a base equivalent, and they are listed so
    # the next reader can check the claim rather than take it:
    #
    #   width / border-collapse      .alv-table (via Bootstrap's .table)
    #   th text-align / weight /     .alv-table thead th, which also paints a
    #     size / tracking / padding    --alv-surface band instead of leaving
    #                                  the heading on paper white
    #   th position:sticky; top:0    .alv-table thead th, identically
    #   td padding / border / ink    .alv-table tbody td
    #   tr:last-child td             base uses border-TOP, so the last row
    #                                needs no special case at all
    #   td.num                       .alv-table .num - same right-align and
    #                                the same font-variant-numeric
    #
    # a.ia-link has no base equivalent and is NOT deleted - it is rescoped,
    # because it was anchored to the table's old class name.
    f = sub1(f, """  table.ia-tbl{width:100%;border-collapse:collapse;font-size:12.5px;}
  table.ia-tbl th{text-align:left;color:var(--alv-ink-faint);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.03em;padding:9px 16px;border-bottom:1px solid var(--alv-line);position:sticky;top:0;background:var(--alv-paper);}
  table.ia-tbl td{padding:10px 16px;border-bottom:1px solid var(--alv-line-soft);color:var(--alv-ink-soft);vertical-align:top;}
  table.ia-tbl tr:last-child td{border-bottom:none;}
  table.ia-tbl td.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums;}
  table.ia-tbl a.ia-link{color:var(--alv-accent-ink);text-decoration:none;font-weight:700;}
  table.ia-tbl a.ia-link:hover{text-decoration:underline;}
  .ia-empty-row{padding:20px 16px;color:var(--alv-ink-faint);font-size:12.5px;}
""",
             """  /* THE DRILL TABLE IS BASE'S NOW - 5 Sep. Thirteen rules went: eight
     here and five more in the phone block that rebuilt the same cards
     base already builds. drillRows() was ALREADY writing data-label and
     class="num", which are base's conventions, so this was a rename and
     eight deletions rather than a rebuild.

     THE HEADING STILL STICKS. That was the open question, because base
     drives its heading shadow from an observer that runs once at page
     load with the VIEWPORT as its root - and this table is built long
     after load and scrolls inside the dialog. But the stickiness is
     plain CSS on .alv-table thead th and pins against the nearest
     scrolling ancestor, which is .ia-drill-body. Measured, not assumed.

     WHAT IS MISSING IS ONLY THE SHADOW under the pinned heading, and it
     was rendered on and off before being given up: the dialog already
     has a hard edge, a title bar and a shadow of its own, so the hint
     has nothing left to say here. Absent BY DECISION - not a sign that
     base's table misbehaves in a dialog.

     NO .table-container EITHER. It exists to give a page card its
     background, radius and shadow and to be the hook .is-stuck toggles;
     the dialog supplies the first and clips the second, and we have just
     declined the third. Rendered both ways: identical, sticky in both.

     THIS RULE IS RESCOPED, NOT NEW. It read `table.ia-tbl a.ia-link`,
     anchored to the class that just changed - so renaming the table
     dropped every issue link back to Bootstrap blue. The first render
     showed exactly that. A rename is not a rename while another selector
     is anchored to the old name. */
  .ia-drill-body .alv-table a.ia-link{color:var(--alv-accent-ink);text-decoration:none;font-weight:700;}
  .ia-drill-body .alv-table a.ia-link:hover{text-decoration:underline;}
""", 'C3: the desktop table rules')

    # =======================================================================
    # 2. the phone block - all five go, base builds the same cards
    # =======================================================================
    f = sub1(f, """    table.ia-tbl thead{display:none;}
    table.ia-tbl,table.ia-tbl tbody,table.ia-tbl tr,table.ia-tbl td{display:block;width:100%;}
    table.ia-tbl tr{border-bottom:1px solid var(--alv-line);padding:6px 0;}
    table.ia-tbl td{border:none;padding:4px 16px;text-align:left !important;}
    table.ia-tbl td::before{content:attr(data-label);display:inline-block;min-width:74px;color:var(--alv-ink-faint);font-size:11px;text-transform:uppercase;letter-spacing:.03em;}
""",
             """    /* THE PHONE CARDS ARE BASE'S TOO. These five rebuilt, selector for
       selector, what .alv-table's own phone block already does - hide the
       thead, block out the cells, prefix each with its data-label. base
       goes one better and promotes the FIRST cell to a card title at
       16px/600, which is the property name here. */
""", 'C3: the phone card rules')

    # =======================================================================
    # 3. drillRows() - the two strings that name the old table
    # =======================================================================
    # EDITING INSIDE A <script>, WHICH THIS PROJECT NORMALLY REFUSES TO DO.
    # The button sweep blanks script blocks on purpose: a class name in a
    # string has no wrapper to say what it is, and a wrong guess edits working
    # JavaScript. That rule is about SWEEPS. This is two named strings in one
    # function that was read first, and the suite renders the result rather
    # than trusting the edit.
    f = sub1(f,
             """    if(!list.length) return '<div class="ia-empty-row">No issues.</div>';""",
             """    if(!list.length) return '<div class="alv-empty">'+
      '<i class="fas fa-clipboard-check"></i>'+
      '<div class="alv-empty-title">No issues</div>'+
      '<div class="alv-empty-hint">Nothing in this band for the period '+
      'selected.</div></div>';""",
             'C3: the empty state')

    f = sub1(f,
             """    return '<table class="ia-tbl"><thead>""",
             """    return '<table class="table alv-table"><thead>""",
             'C3: the table class')

    # ===================================================================
    # 4. C1's note points at rules that no longer exist
    # ===================================================================
    # Not wrong - it is HISTORY, and accurate history: it records that the
    # palette was declared four times and that copy 3 lived in "the .ia-drill
    # and table.ia-tbl rules further down". But "further down" is a pointer,
    # in the present tense, and after this round it points at nothing. A
    # reader following it finds no such rules and has to work out whether the
    # note is stale or the file is broken.
    #
    # Corrected the way base's .alv-seg note was on 2 Sep: the history is left
    # standing and one line is added saying what happened to it since. A note
    # that lies is worse than no note; a note that has been kept up is the
    # only kind worth writing.
    f = sub1(f, """     All four are gone. base's :root tokens are the one source, and the
     script below reads those same tokens rather than restating them. */""",
             """     All four are gone. base's :root tokens are the one source, and the
     script below reads those same tokens rather than restating them.

     AMENDED 5 Sep. "table.ia-tbl rules further down" no longer exist -
     round C3 moved that table onto base's .alv-table and deleted all
     twelve of them. The account above is left as written because it is the
     record of what copy 3 WAS; this line is here so the pointer does not
     send the next reader looking for rules that have gone. */""",
             'C3: keep C1\'s note pointing somewhere real')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
_nc = re.sub(r'/\*.*?\*/', '', f, flags=re.S)
_nc = re.sub(r'<!--.*?-->', '', _nc, flags=re.S)
_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', _nc, re.S))
_js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', _nc, re.S))

# THE OLD NAME IS GONE EVERYWHERE - stylesheet, script and markup. A rename
# that leaves one selector behind is the defect the first render caught.
want('ia-tbl' not in _nc, 'C3: ia-tbl survives outside a comment')
want('ia-empty-row' not in _nc, 'C3: .ia-empty-row survives')
want('class="table alv-table"' in _js, 'C3: drillRows does not build base\'s table')
want('alv-empty-title' in _js, 'C3: the empty state did not migrate')

# THE LINK RULE MUST HAVE COME BACK. Deleting it and not rescoping it is the
# silent half of this round: the links keep working, they just turn blue.
want('.ia-drill-body .alv-table a.ia-link{' in _css,
     'C3: the link rule was deleted rather than rescoped')
want(_css.count('a.ia-link') == 2,
     'C3: expected the link rule and its hover, got %d'
     % _css.count('a.ia-link'))

# WHAT MUST SURVIVE. The overlay is deliberately still local, and deleting
# its rules with the table's would leave the dialog unstyled.
for sel in ('.ia-drill-overlay{', '.ia-drill{', '.ia-drill-head{',
            '.ia-drill-body{', '.ia-desc{'):
    want(sel in _css, 'C3: the overlay lost %s' % sel)
want('.ia-drill-overlay{padding:0' in _css.replace('\n', ''),
     'C3: the overlay lost its phone rule')

# The script's own hooks. Losing one leaves a dialog that renders and does
# nothing - the same failure mode the Notify round guarded against.
for hook in ('iaDrillOverlay', 'iaDrillBody', 'iaDrillClose', 'iaDrillTitle',
             'iaDrillCount', 'iaDrillTag', 'showDrill', 'closeDrill',
             'drillRows'):
    want(hook in _js, 'C3: the script hook %s was lost' % hook)

# THE DELTA, measured against the BACKUP when there is one - on a second run
# F_ORIG is already the patched file.
_before = F_ORIG.replace('\r\n', '\n')
_bak = IA + '.bak_iadrill'
if os.path.exists(_bak):
    _before = load(_bak)[2]
_b_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                              re.sub(r'/\*.*?\*/', '', _before, flags=re.S),
                              re.S))
# RULE OPENINGS, not string occurrences - see the note in the docstring.
_was = len(re.findall(r'(?m)^\s*table\.ia-tbl[^{\n]*\{', _b_css))
want(_was == 12, 'C3: expected 12 ia-tbl rules before, saw %d' % _was)
want(len(re.findall(r'table\.ia-tbl', _css)) == 0,
     'C3: an ia-tbl selector survives')

# base must actually define what the round now leans on, or the table
# renders as unstyled rows and nothing fails.
_bcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', load(BASE)[2], re.S))
for need in ('.alv-table thead th', '.alv-table tbody td', '.alv-empty',
             '.alv-empty-title', '.alv-empty-hint'):
    want(need in _bcss, 'base does not define %s' % need)
want(re.search(r'\.alv-table thead th\s*\{[^}]*position:\s*sticky', _bcss)
     is not None,
     'base\'s table heading is not sticky - the round\'s premise is wrong')

# PROSE THAT CONTAINS MARKUP IS MARKUP. A CSS comment spelling a script tag
# makes a block-slicing scanner parse prose as JavaScript.
for _m in re.finditer(r'/\*.*?\*/', f, re.S):
    want(not re.search(r'</?(?:script|style)\b', _m.group(0)),
         'C3: a CSS comment spells a script or style tag')
for blk in re.findall(r'<style[^>]*>(.*?)</style>', f, re.S):
    want(blk.count('{') == blk.count('}'), 'C3: unbalanced braces')
want(len(re.findall(r'<script[^>]*>', f)) == len(re.findall(r'</script>', f)),
     'C3: a script tag is unbalanced')

# ===========================================================================
# 4b. SECTION 4b - the SCOPE GUARD, NINTH and TENTH occurrences
# ===========================================================================
# The ninth is the best kind, and the FOURTH guard this project has written
# that NAMES the round which would invalidate it. test_ia_tiles.py section 5
# says, in as many words:
#
#     check('the .ia-drill overlay and its table are untouched - C3',
#           'table.ia-tbl{' in FC and '.ia-drill{' in FC)
#
# That was C2 asserting it stayed in its lane. The claim was right and the
# work it pointed at has now happened.
#
# Following the refinement the EIGHTH occurrence forced: split the claim by
# what it is actually about. The OVERLAY is still local and still untouched -
# that half stays on the LIVE file, because it is a claim about today. The
# TABLE half is historical, so it moves onto the snapshot this round leaves,
# and gains a FORWARD half saying C3 did the work rather than that the check
# merely stopped applying.
SUITES = []
TT = os.path.join(ROOT, 'test_ia_tiles.py')
if not os.path.exists(TT):
    print('  test_ia_tiles.py not found - skipping its 4b')
else:
    T_ORIG, T_CRLF, tt = load(TT)
    if 'bak_iadrill' in tt:
        print('  test_ia_tiles.py already patched')
    else:
        _a = """check('the .ia-drill overlay and its table are untouched - C3',
      'table.ia-tbl{' in FC and '.ia-drill{' in FC)"""
        _n = """# MOVED 5 Sep - the SCOPE GUARD, ninth time in this project, and the fourth
# guard written NAMING the round that would invalidate it. This read
# `'table.ia-tbl{' in FC and '.ia-drill{' in FC`: C2 asserting it stayed in
# its lane and left the drill-down to C3. C3 has landed, and moved that table
# onto base's .alv-table.
#
# Split by what each half is a claim ABOUT, which is the refinement the eighth
# occurrence forced. The OVERLAY is still hand-rolled and still local - a
# claim about today, so it stays on the live file. The TABLE is history, so it
# moves onto the snapshot C3 leaves, and gains a forward half: a guard that
# only ever loosens asserts nothing.
check('the .ia-drill overlay is STILL hand-rolled and still local - base has '
      'no modal component, and this is a dialog inside one',
      '.ia-drill{' in FC and '.ia-drill-overlay{' in FC)
_C3 = os.path.join(T, 'fsr.html.bak_iadrill')
if not os.path.exists(_C3):
    check('C3 left a snapshot to measure the old claim against', False,
          'fsr.html.bak_iadrill')
else:
    check('C2 did not touch the drill TABLE - measured on fsr.html.bak_iadrill',
          'table.ia-tbl{' in nocomment(read(_C3)))
    check('  and C3 has since moved it onto base',
          'table.ia-tbl' not in FC
          and 'class="table alv-table"' in FC)"""
        if tt.count(_a) != 1:
            FAIL.append('test_ia_tiles.py: its C3 guard did not match once')
        else:
            tt = tt.replace(_a, _n, 1)
            try:
                compile(tt, 'test_ia_tiles.py', 'exec')
            except SyntaxError as _e:
                FAIL.append('test_ia_tiles.py: the patch does not parse - %s'
                            % _e)
            SUITES.append((TT, T_ORIG, T_CRLF, tt))
            print('  test_ia_tiles.py        C3 guard split and moved')

# The TENTH is the plain kind, and the same one the Financials round moved:
# test_print_leaks.py asserts per file that the print round changed "ONLY the
# guard", measured live against .bak_leak. fsr.html is one of its 34 targets
# and this round edits it, so that comparison would now see C3's work and
# report the print round as having done something it did not. The LATER map
# already exists for exactly this; it gains one line.
TP = os.path.join(ROOT, 'test_print_leaks.py')
if not os.path.exists(TP):
    print('  test_print_leaks.py not found - skipping its 4b')
else:
    P_ORIG, P_CRLF, tp = load(TP)
    # THE MARKER MUST NAME THE MAP, NOT THE FILE. `"'fsr.html'" in tp` matched
    # on the first try - because fsr.html is one of that suite's 34 TARGETS,
    # listed a hundred lines above the map this round edits. A marker that
    # reads the whole file catches the data as readily as the code.
    if "'fsr.html': '.bak_iadrill'" in tp:
        print('  test_print_leaks.py already patched')
    else:
        _a2 = "LATER = {'finance/financial_indicators.html': '.bak_fiseg'}"
        _n2 = ("LATER = {'finance/financial_indicators.html': '.bak_fiseg',\n"
               "         # C3 moved the drill table onto base, 5 Sep.\n"
               "         'fsr.html': '.bak_iadrill'}")
        if tp.count(_a2) != 1:
            FAIL.append('test_print_leaks.py: its LATER map did not match once')
        else:
            tp = tp.replace(_a2, _n2, 1)
            try:
                compile(tp, 'test_print_leaks.py', 'exec')
            except SyntaxError as _e:
                FAIL.append('test_print_leaks.py: the patch does not parse - %s'
                            % _e)
            SUITES.append((TP, P_ORIG, P_CRLF, tp))
            print('  test_print_leaks.py     fsr.html added to its LATER map')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    # BYTES, not characters - len() of a str counts characters and this file
    # carries multi-byte dashes in its comments.
    print('  %-24s %d -> %d bytes'
          % (os.path.basename(p), len(orig.encode('utf-8')),
             len(out.encode('utf-8'))))
    if CHECK:
        return
    bak = p + '.bak_iadrill'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(IA, F_ORIG, F_CRLF, f, DONE)
for _p, _o, _c, _t in SUITES:
    save(_p, _o, _c, _t, False)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
