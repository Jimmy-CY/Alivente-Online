# -*- coding: utf-8 -*-
"""apply_lines_table.py - round IN-2, 11 Oct 2026.

TWO PAGES WROTE THE SAME LINE TABLE. BASE SAYS IT ONCE, AND SAYS WHAT IT
DOES ON A PHONE.

customer_invoice_form.html and physical_invoice_edit.html both carry an
editable invoice line grid - Service, Unit, Description, Qty, Unit Price,
VAT, and a remove button. Both declare the same three rules, and measured
they are IDENTICAL CHARACTER FOR CHARACTER:

    .lines-scroll        overflow-x: auto, paper, 8px radius, a shadow
    .lines-table         margin-bottom: 0; min-width: 720px
    .lines-table thead th  ink ground, 13px, 600

base declares none of them. That is D-4's case again, and it clears the
bar D-3 and D-5 both closed on - A COMPONENT WITH ONE CALLER IS NOT A
COMPONENT YET. This one has two.

WHAT THE RECORDED DEFECT SAID, AND WHAT IS ACTUALLY TRUE
--------------------------------------------------------
IN-2 was recorded as "Invoice Lines force ~364px of sideways scroll".
THE PAGE DOES NOT SCROLL. Both pages wrap the table in their own
`.lines-scroll { overflow-x: auto }`, so the BOX scrolls and the page
stays put. Measured at 390px: page 0px, box 362px.

The first measurement I took reported 0px of page scroll for every
option and nearly went in the notes as a result. It was true and
meaningless - I was measuring the page when the thing that scrolls is
the box. The same shape as the print round's vacuous 1280px viewport.

What IS wrong is subtler and still worth fixing: on a phone you see
Service, Unit and half of Description. Qty, Unit Price and VAT - THE
NUMBERS - are off the edge, and nothing on screen says they exist.

SO ON A PHONE EACH LINE BECOMES A LABELLED BLOCK. Nothing is hidden and
every field carries its own name. It costs height - 980px for two lines
against 151px - and that was his call with both renders in front of him,
against the cheaper option of pinning a column and adding a swipe cue.

THE LABELS COME FROM data-label, AND THE TEMPLATE CARRIES THEM TOO
------------------------------------------------------------------
The stacked view names each field with `content: attr(data-label)`, so
every cell needs the attribute. Both pages build new lines by cloning a
`<template id="lineTemplate">`, which means A ROW ADDED AFTER THE PAGE
LOADED COMES FROM THE TEMPLATE. Label only the server-rendered rows and
every line the user adds on a phone is a column of unlabelled boxes -
the defect would appear only after an interaction, which is exactly the
kind no screenshot catches.

So the template's cells are labelled as well, and the suite asserts it.

WHAT IS LEFT, NAMED
-------------------
THE SHADOW IS STILL A LITERAL. `0 2px 8px rgba(0,0,0,0.06)` moves into
base unchanged, because base has no shadow token to move it to - it
writes its shadows as literals too. A shadow scale is its own decision
and this round does not invent one. The radius does move: D-12 put
`--alv-radius` in reach and 8px is exactly it.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_lines'
SUITE = 'test_lines_table.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
DR2 = 'test_dr2_spelling.py'
DV = 'test_dr2_values.py'
PC = 'test_pair_contrast.py'
RS = 'test_recipe_spice.py'
CHECK = False

PAGES = ('customer_invoice_form.html', 'physical_invoice_edit.html')

# The three blocks, exactly as both pages spell them.
BLOCKS = (
    '.lines-scroll { overflow-x: auto; background: var(--alv-paper); '
    'border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }\n',
    '.lines-table { margin-bottom: 0; min-width: 720px; }\n',
    '.lines-table thead th { background-color: var(--alv-ink); '
    'color: var(--alv-on-accent); font-weight: 600; font-size: 13px; '
    'vertical-align: middle; }\n',
)

BASE_ANCHOR = '      /* ===== /DD-1 ===== */\n'

GUARD = '''
      /* ===== IN-2 ===== 11 Oct 2026 ==================================
         THE INVOICE LINE GRID, SAID ONCE.

         customer_invoice_form and physical_invoice_edit both wrote
         these three rules and wrote them identically, character for
         character. Two callers is what D-3 and D-5 were waiting for.

         ON A PHONE IT STOPS BEING A TABLE. The grid is 720px wide and
         a phone is 390: measured, 362px of it sat outside the box with
         nothing on screen to say so, and what was outside was Qty,
         Unit Price and VAT. A scroll you cannot see is worse on a form
         you fill in than on one you read.

         So each line becomes a labelled block. It costs height - 980px
         for two lines against 151 - and that was chosen from the two
         renders, against pinning a column and adding a swipe cue.

         EVERY CELL CARRIES data-label, INCLUDING THE TEMPLATE'S. Both
         pages add lines by cloning <template id="lineTemplate">, so a
         row added after load comes from there. Labelling only the
         server-rendered rows would leave every line the user adds as a
         column of unnamed boxes - a defect that appears only after an
         interaction.
                                            [test_lines_table.py] */
      .lines-scroll {
        overflow-x: auto;
        background: var(--alv-paper);
        border-radius: var(--alv-radius);
        /* A literal, and deliberately. base writes its own shadows as
           literals - there is no shadow token to move this to, and a
           shadow scale is a decision of its own. */
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      }
      .lines-table { margin-bottom: 0; min-width: 720px; }
      .lines-table thead th {
        background-color: var(--alv-ink);
        color: var(--alv-on-accent);
        font-weight: 600;
        font-size: 13px;
        vertical-align: middle;
      }

      @media screen and (max-width: 768px) {
        .lines-scroll {
          overflow-x: visible;
          background: transparent;
          box-shadow: none;
          border-radius: 0;
        }
        .lines-table,
        .lines-table tbody,
        .lines-table tr,
        .lines-table td { display: block; width: 100%; }
        .lines-table { min-width: 0; border: 0; }
        .lines-table thead { display: none; }
        .lines-table tr {
          border: 1px solid var(--alv-line);
          border-radius: var(--alv-radius);
          padding: 12px 14px;
          margin-bottom: 12px;
          background: var(--alv-paper);
        }
        .lines-table td { border: 0; padding: 0 0 10px; }
        .lines-table td:last-child { padding: 0; text-align: right; }
        .lines-table td[data-label]::before {
          content: attr(data-label);
          display: block;
          font-size: 12px;
          color: var(--alv-ink-soft);
          margin-bottom: 4px;
        }
      }
      /* ===== /IN-2 ===== */
'''

N_PAGES = 2
N_BLOCKS = 6          # 3 on each page
N_LABELLED = 24       # 6 named columns x 2 rows x 2 pages
N_BARE = 4            # the remove-button cell, 1 per row


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('IN-2 REFUSED: %s' % msg)


def headers_of(text):
    """The column names, READ FROM THE PAGE rather than typed here.

    A label typed into the patcher is a second copy of the header, and
    the label-fit round already found one field wearing four different
    names because four places each kept their own.
    """
    m = re.search(r'<thead>(.*?)</thead>', text, re.S)
    if not m:
        return []
    out = []
    for th in re.findall(r'<th\b[^>]*>(.*?)</th>', m.group(1), re.S):
        out.append(' '.join(re.sub(r'<[^>]+>|\{%.*?%\}', '', th).split()))
    return out


def label_row(row, heads):
    """Give each cell its own column's name. The last cell gets none."""
    cells = list(re.finditer(r'<td\b([^>]*)>', row))
    if len(cells) != len(heads):
        return None, 0
    out, last, n = [], 0, 0
    for i, m in enumerate(cells):
        out.append(row[last:m.start()])
        attrs = m.group(1)
        name = heads[i]
        if name and 'data-label' not in attrs:
            out.append('<td data-label="%s"%s>' % (name, attrs))
            n += 1
        else:
            out.append(m.group(0))
        last = m.end()
    out.append(row[last:])
    return ''.join(out), n


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    sys.path.insert(0, root)
    import alv_tree as T

    base_p = T.path_of('base.html')

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED FIRST, BEFORE ANY SURVEY.
    if '===== IN-2 =====' in read(base_p):
        print('IN-2  already applied')
        return 0

    if not os.path.isfile(SUITE):
        refuse('%s is not on disk - the suite ships with the round' % SUITE)

    # ---------------------------------------------------------------- 1
    b = read(base_p)
    if b.count(BASE_ANCHOR) != 1:
        refuse('base.html does not hold the DD-1 close marker exactly once')
    for blk in ('.lines-scroll', '.lines-table'):
        if blk in b:
            refuse('base.html already mentions %s' % blk)
    nb = b.replace(BASE_ANCHOR, BASE_ANCHOR + GUARD, 1)

    # ---------------------------------------------------------------- 2
    edits = {}
    n_blocks = n_lab = n_bare = 0
    shape = None
    for rel in PAGES:
        p = T.path_of(rel)
        t = read(p)

        heads = headers_of(t)
        if len(heads) != 7 or heads[-1] != '':
            refuse('%s: expected 7 columns with the last unnamed, got %r'
                   % (rel, heads))
        if shape is None:
            shape = heads
        elif heads != shape:
            refuse('the two pages no longer agree on the columns: %r vs %r'
                   % (shape, heads))

        for blk in BLOCKS:
            if t.count(blk) != 1:
                refuse('%s: the block %r is not present exactly once'
                       % (rel, blk[:34]))
            t = t.replace(blk, '', 1)
            n_blocks += 1

        for name, pat in (('tbody', r'(<tbody id="linesBody">)(.*?)(</tbody>)'),
                          ('template',
                           r'(<template id="lineTemplate">)(.*?)(</template>)')):
            m = re.search(pat, t, re.S)
            if not m:
                refuse('%s: no %s to label - the round cannot leave half the '
                       'rows unnamed' % (rel, name))
            body, n = label_row(m.group(2), heads)
            if body is None:
                refuse('%s: the %s row does not have one cell per column'
                       % (rel, name))
            n_lab += n
            n_bare += 1
            t = t[:m.start()] + m.group(1) + body + m.group(3) + t[m.end():]

        edits[p] = t

    if n_blocks != N_BLOCKS:
        refuse('removed %d block(s), expected %d' % (n_blocks, N_BLOCKS))
    if n_lab != N_LABELLED:
        refuse('labelled %d cell(s), expected %d' % (n_lab, N_LABELLED))
    if n_bare != N_BARE:
        refuse('%d row(s) seen, expected %d' % (n_bare, N_BARE))

    # A ROUND THAT CHANGES A NUMBER OWNS EVERY NUMBER THAT COUNTS IT -
    # and this round changes one and exposes an asymmetry in another.
    #
    # CONVERTED_N: this round's suite joins the register, so 51 becomes
    # 52. PQ-1's suite now reads that constant against the live list
    # rather than against a literal, so it catches a stale one and says
    # what the live value is. That rewrite was LB-1's, one round ago,
    # and this is the first round it has caught. It worked.
    wd = read(WD)
    old_n = 'CONVERTED_N = 51'
    if wd.count(old_n) != 1:
        refuse('%s does not pin CONVERTED_N at 51 - LB-1 must be applied'
               % WD)
    nwd = wd.replace(
        old_n,
        'CONVERTED_N = 52   # IN-2, 11 Oct 2026 - test_lines_table joins'
        '   # (was 51)', 1)

    # DR-2's suite READ BASE LIVE AND THE PAGES FROZEN.
    #
    #   bsrc = read(base)                  <- whatever base says today
    #   s    = as_left_by(page, SUFFIX)    <- the page as DR-2 left it
    #
    # So a later round that LIFTS a declaration into base makes DR-2's
    # suite fail: base now says what the frozen page still says, and the
    # check calls that drift. It is drift this round REMOVED. Six of them
    # - .lines-scroll background and border-radius, .lines-table thead th
    # color, on both pages.
    #
    # as_left_by exists so a later round cannot break an older suite, and
    # it was being applied to one side only. Reading base the same way
    # judges DR-2's claim entirely at DR-2's moment, which is what the
    # whole mechanism is for.
    dr = read(DR2)
    old_b = ("bsrc = read(alv_tree.path_of('base.html'))\n")
    if dr.count(old_b) != 1:
        refuse('%s does not read base where this round expects' % DR2)
    ndr = dr.replace(
        old_b,
        "# IN-2, 11 Oct 2026 - THROUGH now(), LIKE THE PAGES.\n"
        "# This read base LIVE while reading every page as DR-2 left it,\n"
        "# so a later round lifting a declaration INTO base made this\n"
        "# check fail on drift that the lift had just removed. One side\n"
        "# frozen and the other moving is not a comparison. Judged at\n"
        "# DR-2's own moment, both sides agree again.\n"
        "bsrc = now(alv_tree.path_of('base.html'))\n", 1)

    # THE SAME FAULT AGAIN, IN DR-2's OTHER SUITE.
    #
    # test_dr2_values section 4 reads every page through now() - as DR-2
    # left it - and then compares it against `bsrc = read(base)`, base as
    # it is today. Lifting .lines-scroll and .lines-table thead th into
    # base therefore shows up as six new drift entries on pages that no
    # longer declare them at all.
    #
    # Identical to the fix above. A SUITE THAT FREEZES ONE SIDE OF A
    # COMPARISON AND LETS THE OTHER MOVE IS NOT COMPARING ANYTHING.
    dv = read(DV)
    old_bs = "bsrc = read(alv_tree.path_of('base.html'))\n"
    if dv.count(old_bs) != 1:
        refuse('%s does not read base where this round expects' % DV)
    ndv = dv.replace(
        old_bs,
        "# IN-2, 11 Oct 2026 - THROUGH now(), LIKE THE PAGES. Section 4\n"
        "# compared live base against pages frozen at DR-2, so a later\n"
        "# round LIFTING a declaration into base was reported here as\n"
        "# drift - on pages that had just stopped declaring it. The same\n"
        "# one-sided comparison as test_dr2_spelling, two suites apart.\n"
        "bsrc = now(alv_tree.path_of('base.html'))\n", 1)

    # AND THE PAIR COUNT, WHICH THIS ROUND MOVES - DOWNWARDS.
    #
    # test_pair_contrast counts every rule setting both a background and
    # a colour. `.lines-table thead th` sets both, and it came off TWO
    # pages and went into base ONCE, so the census falls by one. I
    # assumed it would rise; it is 712, and measuring is why this says
    # 712 rather than 714.
    pc = read(PC)
    old_pairs = 'EXPECT_PAIRS = 713'
    if pc.count(old_pairs) != 1:
        refuse('%s does not pin EXPECT_PAIRS at 713' % PC)
    npc = pc.replace(
        old_pairs,
        'EXPECT_PAIRS = 712   # IN-2, 11 Oct 2026 - .lines-table thead th\n'
        '# sets a background AND a colour. It came off two pages and went\n'
        '# into base once, so the census FALLS by one.   # (was 713)', 1)

    # AND THE SECOND COPY OF THAT CENSUS.
    #
    # test_recipe_spice carries its own literal `n == 713`. RC-2's claim
    # there is "RC-2 left the census where it found it" - a fact about
    # RC-2 - and writing it as a literal made it a claim about the census
    # instead, which any later round can falsify by doing its job. IN-2
    # is that round.
    #
    # Rewritten the way LB-1 rewrote PQ-1's counters: it reads the number
    # out of the suite that owns it. Then the two can never disagree, and
    # no round after this one has to edit a second copy.
    rs = read(RS)
    old_rs = ('ok(n == 713,\n'
              "   'and still %d pairs in all - NOT ONE LEFT THE CENSUS, "
              "which is the '\n"
              "   'whole point of section 7' % n)\n")
    if rs.count(old_rs) != 1:
        refuse('%s does not pin the pair census where this round expects'
               % RS)
    ndw_rs = rs.replace(
        old_rs,
        "# IN-2, 11 Oct 2026 - READ FROM THE SUITE THAT OWNS THE CENSUS,\n"
        "# not copied. This said `n == 713`, and 713 was true until a\n"
        "# later round legitimately moved it - IN-2 took .lines-table\n"
        "# thead th off two pages and put it in base once, so the census\n"
        "# FELL by one. RC-2's claim was that RC-2 left the census where\n"
        "# it found it, which is still true; the literal was what made it\n"
        "# read as a claim about the number.\n"
        "_pc = re.search(r'EXPECT_PAIRS = (\\d+)',\n"
        "                read(os.path.join(ROOT, 'test_pair_contrast.py')))\n"
        "_pc = int(_pc.group(1)) if _pc else -1\n"
        "ok(n == _pc,\n"
        "   'and the census still reads %d, the same number "
        "test_pair_contrast '\n"
        "   'pins - RC-2 took nothing out of it' % n, '%s vs %s'"
        " % (n, _pc))\n", 1)

    # ---------------------------------------------------------------- 3
    tree = read(TREE)
    conv = "    'test_label_weight.py',\n]"
    if tree.count(conv) != 1:
        refuse('alv_tree.CONVERTED does not end where this round expects - '
               'LB-1 must be applied and still be last')
    ntree = tree.replace(
        conv,
        "    'test_label_weight.py',\n"
        "    # IN-2, 11 Oct 2026 - wide from birth: it reads two named\n"
        "    # templates and base through alv_tree, and builds no root.\n"
        "    'test_lines_table.py',\n]", 1)

    rounds = read(ROUNDS)
    r_anchor = "    '.bak_lblwt',\n"
    if rounds.count(r_anchor) != 1:
        refuse('alv_rounds.ROUNDS does not end with LB-1 - it must be '
               'applied and still be last')
    nrounds = rounds.replace(r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(PS1)
    p_anchor = "    'test_label_weight.py'\n)"
    if ps.count(p_anchor) != 1:
        refuse('the $suites anchor is not in %s exactly once - LB-1 must be '
               'applied and still be last' % PS1)
    nps = ps.replace(p_anchor,
                     "    'test_label_weight.py',\n    '%s'\n)" % SUITE, 1)

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('')
        print('IN-2  check only - nothing written')
        print('IN-2  would move %d block(s) off %d page(s) into base'
              % (n_blocks, N_PAGES))
        print('IN-2  would label %d cell(s), the template\'s included'
              % n_lab)
        print('IN-2  columns read from the pages: %s'
              % ', '.join(x for x in shape if x))
        return 0

    for p, t in [(base_p, nb)] + list(edits.items()) \
            + [(os.path.join(root, WD), nwd),
               (os.path.join(root, DR2), ndr),
               (os.path.join(root, DV), ndv),
               (os.path.join(root, PC), npc),
               (os.path.join(root, RS), ndw_rs),
               (os.path.join(root, TREE), ntree),
               (os.path.join(root, ROUNDS), nrounds),
               (os.path.join(root, PS1), nps)]:
        backup(p)
        write(p, t)

    print('')
    print('IN-2  base takes the invoice line grid - %d block(s) off %d page(s)'
          % (n_blocks, N_PAGES))
    print('IN-2  and says what it does on a phone: each line becomes a')
    print('IN-2  labelled block, so nothing sits off the edge unannounced')
    print('IN-2  %d cell(s) labelled across %d row(s) - the <template> rows'
          % (n_lab, n_bare))
    print('IN-2  included, because that is where a line added after load')
    print('IN-2  comes from')
    print('IN-2  CONVERTED 51 to 52, and DR-2 now reads base the way')
    print('IN-2  it already read the pages - as the round left it, and so')
    print('IN-2  does DR-2 values. The pair census falls 713 to 712.')
    print('IN-2  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
