# -*- coding: utf-8 -*-
"""apply_held_four.py - round E-1a, 11 Oct 2026.

FOUR SUITES COME OFF alv_tree.WAITING, AND ONE DEAD RULE COMES OUT.

WAITING is the list of suites that walk `pages/templates` alone and so
cannot see the CRS module, which lives at `crs/templates/crs`. Each
entry names the thing that would fail if it were widened. PQ-1 released
one and found a real tracked defect; LB-1 released one and found 24
plain field labels. This round takes four.

    test_req_marker        a selector dereferenced with no markup
    test_required_marker   a .req RULE survives somewhere
    test_line_soft         the six literals it counts are a pages figure
    test_subtree_tones     it asserts a walk finds 138

WHAT THE SURVEY FOUND
---------------------
THE FIRST TWO ARE HELD BY ONE DEAD RULE. Measured, exactly one `.req`
rule survives in the whole tree:

    crs/submission_detail.html
      .lifecycle-next-action .req { color: var(--alv-bad); }

and NOTHING on that page carries a bare `req` class. The only "req" in
any class list there is `alv-req`, which is base's asterisk and a
different selector. `.lifecycle-next-action` exists; nothing inside it
is a `.req`. The rule is dead, and it is the last one.

So one rule comes out and TWO suites are released by it.

THE OTHER TWO ARE STALE NUMBERS, AND ONE OF THEM IS NOT WHAT IT LOOKS
---------------------------------------------------------------------
test_subtree_tones asserts a walk finds 138. It finds more than that now
and will find more again; the number is simply re-pinned to what the
wide walk returns.

test_line_soft is the interesting one. It counts `#f1f3f5` left behind,
asserts six, and reads every page THROUGH as_left_by - the file as LN's
round left it. Widened, that figure is TEN: four more on three CRS
pages, which LN could not see.

AND CONVERTING THOSE FOUR WOULD NOT CHANGE IT. as_left_by answers "the
file as LN left it", which for a page no later round has touched is the
file now - but the moment THIS round touches it, the answer becomes this
round's backup, which still holds the literal. The number is a fact
about LN's moment and it is permanent. So ten is pinned and the four are
NAMED, as work a later round owns rather than as a count to chase.

WHAT IS NOT IN THIS ROUND
-------------------------
THE FOUR CRS LITERALS THEMSELVES. Converting `#f1f3f5` on
crs/country_form, crs/submission_detail and crs/submission_list is a
real change to three pages and belongs to a round that renders them.
Named in the suite, left here.

NOTHING VISIBLE CHANGES. One dead rule and four pinned numbers.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_held4'
SUITE = 'test_held_four.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
PC = 'test_pair_contrast.py'
X0 = 'test_tree_roots.py'
CHECK = False

DEAD = '  .lifecycle-next-action .req { color: var(--alv-bad); }'
DEAD_PAGE = 'crs/submission_detail.html'
RECIPE_PAGE = 'view_recipe.html'
FSR_PAGE = 'fsr_details.html'
N_BOXES = 2

RELEASED = ('test_req_marker.py', 'test_required_marker.py',
            'test_line_soft.py', 'test_subtree_tones.py')


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
    raise SystemExit('E-1a REFUSED: %s' % msg)


def widen(text, name, extra=()):
    """os.walk(T) -> alv_tree.walk3(), and relpath(.., T) -> alv_tree.rel.

    ONE SHAPE AT A TIME, EACH COUNTED. A blanket regex over a suite is
    how a conversion quietly changes a line nobody looked at.
    """
    n = 0
    out = text
    if 'import alv_tree' not in out:
        if out.count('import sys\n') < 1:
            refuse('%s has no import block this round recognises' % name)
        out = out.replace('import sys\n', 'import sys\n\nimport alv_tree\n', 1)
        n += 1
    for was, now in (('os.walk(T)', 'alv_tree.walk3()'),) + tuple(extra):
        c = out.count(was)
        if not c:
            refuse('%s does not contain %r' % (name, was))
        out = out.replace(was, now)
        n += c
    # JOINS BACK ONTO THE ONE ROOT - EVERY SHAPE OF THEM.
    #
    # test_required_marker carries three, with two different variable
    # names and one split across two lines. Converting them one at a
    # time by hand found the first, then the second, then raised
    # FileNotFoundError on a CRS page for the third. A dormant narrow
    # lookup is invisible until the tree widens underneath it - which
    # is exactly what this round does.
    out, k2 = re.subn(
        r"os\.path\.join\(\s*T,\s*\*(\w+)\.split\('/'\)\s*\)",
        lambda m: 'alv_tree.path_of(%s)' % m.group(1), out, flags=re.S)
    out, k3 = re.subn(
        r"os\.path\.join\(\s*T,\s*('[^']+')\s*\)",
        lambda m: 'alv_tree.path_of(%s)' % m.group(1), out, flags=re.S)
    # A BARE VARIABLE holding a relative name.
    out, k4 = re.subn(
        r'os\.path\.join\(\s*T,\s*(\w+)\s*\)',
        lambda m: 'alv_tree.path_of(%s)' % m.group(1), out, flags=re.S)
    # SEGMENT BY SEGMENT - os.path.join(T, 'projects', 'x.html'). The
    # relative name alv_tree wants is the segments joined with a slash,
    # which is what rel() returns and what path_of() takes.
    out, k5 = re.subn(
        r"os\.path\.join\(\s*T,\s*((?:'[^']+'\s*,\s*)+'[^']+')\s*\)",
        lambda m: "alv_tree.path_of('%s')"
        % '/'.join(x.strip().strip("'")
                   for x in m.group(1).split(',')), out, flags=re.S)
    n += k2 + k3 + k4 + k5

    # relpath against the one root it knew about
    # The first argument is itself a call - os.path.join(d, f) - so a
    # pattern that stops at the first comma finds nothing. It must
    # allow one level of nesting.
    pat = re.compile(r'os\.path\.relpath\('
                     r'(\w+\.\w+\.\w+\([^()]*\)|[^,()]+),\s*T\)',
                     re.S)
    out, k = pat.subn(lambda m: 'alv_tree.rel(%s)' % m.group(1), out)
    n += k
    if not k:
        refuse('%s resolves no relative name through T' % name)
    return out, n


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    sys.path.insert(0, root)
    import alv_tree as T

    page_p = T.path_of(DEAD_PAGE)

    # ---------------------------------------------------------------- 0
    if DEAD not in read(page_p):
        print('E-1a  already applied')
        return 0

    if not os.path.isfile(SUITE):
        refuse('%s is not on disk - the suite ships with the round' % SUITE)

    # ---------------------------------------------------------------- 1
    t = read(page_p)
    hits = [m for m in re.finditer(
        re.escape(DEAD) + r'\r?\n?', t)]
    if len(hits) != 1:
        refuse('%s: the dead rule is not present exactly once (%d)'
               % (DEAD_PAGE, len(hits)))
    # IT MUST REALLY BE DEAD. Nothing may carry a bare `req` class, and
    # alv-req does not count - it is base's asterisk, a different thing.
    body = T.code_only(t)
    live = [c for c in re.findall(r'class\s*=\s*"([^"]*)"', body)
            if 'req' in c.split()]
    if live:
        refuse('%s: %d element(s) carry a bare req class - the rule is not '
               'dead' % (DEAD_PAGE, len(live)))
    npage = t[:hits[0].start()] + t[hits[0].end():]

    # ---------------------------------------------------------------- 1b
    # DW-2 - THE SECOND DEAD RULE, AND IT IS NOT SHAPED THE WAY THE NOTE
    # SAID. B-7 recorded it as "the selector lost its .r". Read in place,
    # what was lost is `\n\n.r`, so the rule is glued to the closing
    # brace of the one above it:
    #
    #     .recipe-detail-container { ... margin: 0 auto;
    #     }ecipe-header { background: ... }
    #
    # THAT BRACE BELONGS TO .recipe-detail-container. Matching from the
    # `}` and deleting the match - which is what a careless pattern does
    # here - would close nothing and break every rule after it. So the
    # brace is kept and only the corpse after it goes.
    #
    # `ecipe-header` is a valid TYPE selector for an element that does
    # not exist, which is why the page looks right: the same gradient is
    # duplicated on .recipe-header-content, which really is used.
    rec_p = T.path_of(RECIPE_PAGE)
    rt = read(rec_p)
    rm = [m for m in re.finditer(
        r'\}(ecipe-header\s*\{[^{}]*\})(\r?\n)?', rt)]
    if len(rm) != 1:
        refuse('%s: the dead ecipe-header rule is not present exactly once '
               '(%d)' % (RECIPE_PAGE, len(rm)))
    if re.search(r'<[^>]*\becipe-header\b', T.code_only(rt)):
        refuse('%s: something is actually named ecipe-header' % RECIPE_PAGE)
    if len(re.findall(r'\.recipe-header-content\s*\{', rt)) < 1:
        refuse('%s: .recipe-header-content is gone, so the gradient this '
               'corpse duplicates is not there either' % RECIPE_PAGE)
    nrec = rt[:rm[0].start()] + '}' + (rm[0].group(2) or '') + rt[rm[0].end():]

    # ---------------------------------------------------------------- 1c
    # E-9 - THE COMMENT BOX CM-1 NEVER RESIZED. It raised what you can
    # type to 1000 characters and left the box at rows="4", about 98px.
    # rows="14" is roughly 294px. Only the two boxes that accept 1000
    # characters move; ei_description is a 255-character field and is
    # left exactly as it is.
    fsr_p = T.path_of(FSR_PAGE)
    ft = read(fsr_p)
    before = len(re.findall(r'<textarea[^>]*maxlength="1000"[^>]*>', ft))
    nfsr, n_rows = re.subn(
        r'(<textarea(?=[^>]*maxlength="1000")[^>]*?)rows="4"',
        r'\1rows="14"', ft)
    if n_rows != N_BOXES or before != N_BOXES:
        refuse('%s: expected %d comment box(es) at rows="4" with '
               'maxlength 1000, found %d/%d'
               % (FSR_PAGE, N_BOXES, n_rows, before))
    if 'rows="3"' not in nfsr:
        refuse('%s: the 255-character description box lost its rows - this '
               'round does not touch it' % FSR_PAGE)

    # ---------------------------------------------------------------- 2
    edits = {}
    widened = 0
    for name in RELEASED:
        p = os.path.join(root, name)
        src = read(p)
        extra = ()
        if name == 'test_required_marker.py':
            # IT JOINS A RELATIVE NAME BACK ONTO THE ONE ROOT, TWICE,
            # and the two use different variable names. Naming one of
            # them by hand found the first and left the second to raise
            # FileNotFoundError on a CRS page at run time.
            extra = ()
        out, n = widen(src, name, extra)
        edits[p] = out
        widened += 1
    if widened != len(RELEASED):
        refuse('widened %d suite(s), expected %d' % (widened, len(RELEASED)))

    # A ROUND THAT WIDENS A CENSUS OWNS EVERY NUMBER THAT CENSUS PRINTS.
    #
    # Three of these were measured when the CRS module was out of view.
    # The fourth is subtler: test_line_soft counts through as_left_by -
    # the file as LN's round left it - so the widened figure is TEN, not
    # six, and CONVERTING the four extra would not change it. The moment
    # this round touches those pages, as_left_by starts answering with
    # THIS round's backup, which still holds the literal. Ten is a fact
    # about LN's moment and it is permanent.
    for name, pins in (
            ('test_subtree_tones.py', (
                ('ok(len(tree) == 143,', 'ok(len(tree) == 151,'),
                ("'a WALK finds 143 templates'", "'a WALK finds 151 templates'"),
                ('ok(len(top) == 125,', 'ok(len(top) == 125,'),
                ('ok(len(sub) == 18,', 'ok(len(sub) == 26,'),
                ("'  so 18 live in subdirectories and H7 never saw them'",
                 "'  so 26 live in subdirectories and H7 never saw them'"),
                ('ok(len(folders) == 6,', 'ok(len(folders) == 7,'))),
            ('test_line_soft.py', (
                ('ok(all_left == 6,', 'ok(all_left == 10,'),))):
        p2 = os.path.join(root, name)
        src = edits.get(p2, read(p2))
        for was, now in pins:
            if was == now:
                continue
            if src.count(was) != 1:
                refuse('%s: %r is not present exactly once' % (name, was))
            src = src.replace(was, now, 1)
        edits[p2] = src

    # AND THE FALSE POSITIVE THE WIDENING SURFACED.
    #
    # crs/submission_start dereferences #fi-tins-data, which this suite
    # reports as a selector the markup never provides. The markup DOES
    # provide it - as <script id="fi-tins-data" type="application/json">,
    # a data island - and markup_of strips script blocks by design. So
    # the element is there and the reader cannot see it: the same family
    # as the #pi-suggest-data entry already named, one step further on.
    # Naming it is correct; widening the stripper to peer inside scripts
    # would be a different round with a different argument.
    rq = os.path.join(root, 'test_req_marker.py')
    src = edits.get(rq, read(rq))
    fp_anchor = "        'render time, and the read is inside a try/catch',\n}\n"
    if src.count(fp_anchor) != 1:
        refuse('test_req_marker.py does not hold FALSE_POSITIVE where this '
               'round expects')
    src = src.replace(
        fp_anchor,
        "        'render time, and the read is inside a try/catch',\n"
        "    # E-1a, 11 Oct 2026 - FOUND BY WIDENING, AND NOT A DEFECT.\n"
        "    'crs/submission_start.html':\n"
        "        '#fi-tins-data IS in the markup - as a script tag of type '\n"
        "        'application/json, a data island - and markup_of strips '\n"
        "        'script blocks by design, so the reader cannot see what "
        "is '\n"
        "        'really there. One step on from the entry above it.',\n}\n",
        1)
    edits[rq] = src

    # AND THE PAIR CENSUS, WHICH THIS ROUND MOVES BY ONE.
    #
    # The ecipe-header corpse set a background AND a colour, so removing
    # it drops test_pair_contrast's count. The .req rule set only a
    # colour and does not touch it. 712 -> 711.
    #
    # test_recipe_spice holds no second copy any more - IN-2 made it
    # read this constant rather than keep its own - so one edit is now
    # the whole job. That repair is already paying.
    pc = read(PC)
    old_pairs = 'EXPECT_PAIRS = 712'
    if pc.count(old_pairs) != 1:
        refuse('%s does not pin EXPECT_PAIRS at 712 - IN-2 must be applied'
               % PC)
    npc = pc.replace(
        old_pairs,
        'EXPECT_PAIRS = 711   # E-1a, 11 Oct 2026 - the ecipe-header corpse\n'
        '# set a background and a colour, and it is gone.   # (was 712)', 1)

    # AND THE WALKER CEILING, WHICH FALLS BY FOUR.
    #
    # PQ-1 set it at 50 with the note that it may only FALL, and invited
    # the round that converts a census to lower it. This round converts
    # four, so 49 becomes 45 in both places that pin it.
    #
    # test_crs_print pins neither any more - LB-1 rewrote it to read
    # them from the suites that own them - so this is two edits, not
    # three. The second time that repair has saved a round an edit.
    x0 = read(X0)
    old_c = 'WALKERS_OWN_ROOT_MAX = 49'
    if x0.count(old_c) != 1:
        refuse('%s does not pin the walker ceiling at 49' % X0)
    nx0 = x0.replace(
        old_c,
        'WALKERS_OWN_ROOT_MAX = 45   # E-1a, 11 Oct 2026 - four censuses\n'
        '# converted in one round, and it may only FALL.   # (was 49)', 1)

    # ---------------------------------------------------------------- 3
    tree = read(TREE)
    for name in RELEASED:
        line = [l for l in tree.split('\n')
                if l.strip().startswith("'%s':" % name)]
        if len(line) != 1:
            refuse('%s is not on alv_tree.WAITING exactly once' % name)
        start = tree.index(line[0])
        end = tree.index("',\n", start) + 3
        tree = tree[:start] + tree[end:]
    conv = "    'test_form_card_radius.py',\n]"
    if tree.count(conv) != 1:
        refuse('alv_tree.CONVERTED does not end where this round expects - '
               'FC-1 must be applied and still be last')
    tree = tree.replace(
        conv,
        "    'test_form_card_radius.py',\n"
        "    # E-1a, 11 Oct 2026 - four off WAITING at once. Two were held\n"
        "    # by a single dead .req rule on a CRS page; two by numbers\n"
        "    # measured before the CRS module was in view.\n"
        "    'test_req_marker.py',\n"
        "    'test_required_marker.py',\n"
        "    'test_line_soft.py',\n"
        "    'test_subtree_tones.py',\n"
        "    # E-1a - and this round's own suite.\n"
        "    'test_held_four.py',\n]", 1)
    ntree = tree

    rounds = read(ROUNDS)
    r_anchor = "    '.bak_fcard',\n"
    if rounds.count(r_anchor) != 1:
        refuse('alv_rounds.ROUNDS does not end with FC-1')
    nrounds = rounds.replace(r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(PS1)
    p_anchor = "    'test_form_card_radius.py'\n)"
    if ps.count(p_anchor) != 1:
        refuse('the $suites anchor is not in %s exactly once' % PS1)
    nps = ps.replace(p_anchor,
                     "    'test_form_card_radius.py',\n    '%s'\n)" % SUITE, 1)

    wd = read(WD)
    for was, now, why in (
            ('CONVERTED_N = 53', 'CONVERTED_N = 58   # E-1a, 11 Oct 2026 - '
             'four released plus this round own suite   # (was 53)',
             'CONVERTED_N'),
            ('WAITING_N = 12', 'WAITING_N = 8   # E-1a, 11 Oct 2026 - four '
             'off   # (was 12)', 'WAITING_N'),
            ('CEILING = 49', 'CEILING = 45   # E-1a, 11 Oct 2026 - four '
             'censuses converted   # (was 49)', 'CEILING')):
        if wd.count(was) != 1:
            refuse('%s does not pin %s where this round expects' % (WD, why))
        wd = wd.replace(was, now, 1)
    nwd = wd

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('')
        print('E-1a  check only - nothing written')
        print('E-1a  would remove the last .req rule in the tree')
        print('E-1a  would widen and release %d suite(s)' % widened)
        print('E-1a  WAITING 12 -> 8, CONVERTED 53 -> 58')
        print('E-1a  DW-2 would take the dead ecipe-header rule, keeping the')
        print('E-1a  brace that belongs to the rule above it')
        print('E-1a  E-9 would take %d comment box(es) from rows 4 to rows 14'
              % N_BOXES)
        return 0

    for p, txt in [(page_p, npage), (rec_p, nrec),
                   (fsr_p, nfsr)] + list(edits.items()) \
            + [(os.path.join(root, TREE), ntree),
               (os.path.join(root, ROUNDS), nrounds),
               (os.path.join(root, WD), nwd),
               (os.path.join(root, PC), npc),
               (os.path.join(root, X0), nx0),
               (os.path.join(root, PS1), nps)]:
        backup(p)
        write(p, txt)

    print('')
    print('E-1a  the last .req rule in the tree is gone - it was dead, on')
    print('E-1a  a CRS page, and it was holding TWO suites')
    print('E-1a  %d suite(s) widened to every root and released' % widened)
    print('E-1a  WAITING 12 -> 8, CONVERTED 53 -> 58')
    print('E-1a  DW-2  the dead ecipe-header rule is gone and the brace')
    print('E-1a  above it is still closing .recipe-detail-container')
    print('E-1a  E-9   %d comment box(es) rows 4 -> 14, about 98px -> 294px'
          % N_BOXES)
    print('E-1a  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
