# -*- coding: utf-8 -*-
"""apply_crs_print.py - round PQ-1, 10 Oct 2026.

SIX CRS PAGES PRINT THE PHONE LAYOUT, AND NOTHING COULD SEE THEM.

A4 portrait is about 718 CSS px. A media query written without the
`screen` keyword therefore fires on paper, so a phone rule becomes a
print rule. The house settled that on 21 Sep and every clause in
pages/templates has said `screen` since - 104 of them.

Six CRS pages do not:

    crs/country_list.html        crs/index.html
    crs/fi_form.html             crs/submission_detail.html
    crs/fi_list.html             crs/submission_list.html

One clause each, all six character-identical. Print any of them today
and you get the phone layout.

WHY NOTHING CAUGHT IT. test_print_queries walks pages/templates and
has never seen crs/templates. That is not an oversight - the suite
sits on alv_tree.WAITING, and the reason recorded against it is
exactly "a bare max-width clause outside base". The register knew.
What it could not do was fix it.

SO THE ROUND IS BOTH HALVES. Six one-line edits close the leak; the
suite widening to alv_tree.walk3() is what stops the seventh.

I WIDENED IT FIRST AND WATCHED IT FAIL, which is the standards block's
own instruction for promoting a convention to enforced: a suite
written after the fix has never seen the defect. Widened against the
unfixed tree it read 151 templates instead of 143 and failed on
"no template but base has a bare max-width clause". Then the fix, then
green. The suite has met the thing it guards against.

WHAT MOVES ON THE REGISTER, and why each one has to
---------------------------------------------------
A round that changes a number owns every number that counts it.

  alv_tree.WAITING      loses it   14 -> 13
  alv_tree.CONVERTED    gains it   47 -> 48
  test_waiting_down     WAITING_N, CONVERTED_N and CEILING follow
  test_tree_roots       WALKERS_OWN_ROOT_MAX 51 -> 50

That last one is a ceiling the file says may only FALL, with a note
inviting the next round that converts a census to lower it and lock
the gain in. This is that round.

NOT FIXED HERE: base's own bare clause at 991px. test_print_queries
blesses it by name - on paper it hides the sidebar, which the
print-leak round decided was right. Left exactly as it is.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree as T                                          # noqa: E402

SUFFIX = '.bak_crsprint'
MARK = 'PQ-1, 10 Oct 2026'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_crs_print.py'
ME = 'apply_crs_print.py'
GUARD = 'test_print_queries.py'
CHECK = False

BARE = '@media (max-width: 768px) {'
FIXED = '@media screen and (max-width: 768px) {'
N_PAGES = 6

PAGES = ('crs/country_list.html', 'crs/fi_form.html', 'crs/fi_list.html',
         'crs/index.html', 'crs/submission_detail.html',
         'crs/submission_list.html')

WALK_OLD = """def templates():
    out = []
    for d, _, fs in os.walk(ROOT):
        for f in fs:
            if f.endswith('.html') and 'OLD DO NOT USE' not in f:
                p = os.path.join(d, f)
                out.append((os.path.relpath(p, ROOT).replace('\\\\', '/'), p))
    return sorted(out)"""

WALK_NEW = """def templates():
    # PQ-1, 10 Oct 2026 - THE WHOLE TREE, not one root. This walked
    # pages/templates only, so the eight CRS pages were invisible to
    # it and six of them carried a bare max-width clause that fires on
    # paper. alv_tree.walk3() is the house walk and knows every root.
    out = []
    for d, _, fs in alv_tree.walk3():
        for f in fs:
            if f.endswith('.html') and 'OLD DO NOT USE' not in f \\
                    and '.bak_' not in f:
                q = os.path.join(d, f)
                out.append((alv_tree.rel(q).replace('\\\\', '/'), q))
    return sorted(out)"""


def read(p):
    return open(p, encoding='utf-8', newline='').read()


def write(p, t):
    open(p, 'w', encoding='utf-8', newline='').write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    gp = os.path.join(root, GUARD)
    if MARK in read(gp):
        print('PQ-1  already applied')
        return 0

    # ---- survey, then write ------------------------------------------
    plan = []
    for rel in PAGES:
        p = T.path_of(rel)
        raw = read(p)
        n = T.code_only(raw).count(BARE)
        if n != 1:
            raise SystemExit(
                'PQ-1: %s carries %d bare clause(s) and the round was '
                'measured at exactly one' % (rel, n))
        plan.append((p, rel, raw))

    # AND NOBODY ELSE. If a seventh has appeared since this was
    # measured, the round refuses rather than fixing six and reporting
    # a number that is no longer the whole of it.
    others = []
    for p in sorted(T.templates()):
        rel = T.rel(p).replace(os.sep, '/')
        if rel in PAGES or rel == 'base.html':
            continue
        c = T.code_only(read(p))
        for m in re.finditer(r'@media\s*([^{]+)\{', c):
            q = ' '.join(m.group(1).split())
            if 'screen' not in q and 'print' not in q and 'max-width' in q:
                others.append('%s: @media %s' % (rel, q))
    if others:
        raise SystemExit('PQ-1: %d bare clause(s) outside the six this '
                         'round names: %s' % (len(others), others[:6]))

    for p, rel, raw in plan:
        # THE LITERAL, NOT A REGEX OVER THE WHOLE FILE. These six files
        # are CRLF and the replacement must not smuggle in a bare \n.
        out = raw.replace(BARE, FIXED, 1)
        if BARE in T.code_only(out):
            raise SystemExit('PQ-1: a bare clause survived in %s' % rel)
        if FIXED not in out:
            raise SystemExit('PQ-1: the fix did not land in %s' % rel)
        if not CHECK:
            backup(p)
            write(p, out)

    # ---- the guard grows up ------------------------------------------
    gt = read(gp)
    if gt.count(WALK_OLD) != 1:
        raise SystemExit('PQ-1: %s does not walk its root in the shape '
                         'this round was measured against' % GUARD)
    gout = gt.replace(WALK_OLD, WALK_NEW, 1)
    gout = gout.replace(
        "bb = bare_clauses(read(os.path.join(ROOT, 'base.html')))",
        "bb = bare_clauses(read(alv_tree.path_of('base.html')))")
    gout = gout.replace(
        "base_css = '\\n'.join(styles_of(read(os.path.join(ROOT, "
        "'base.html'))))",
        "base_css = '\\n'.join(styles_of(read(alv_tree.path_of("
        "'base.html'))))")
    gout = gout.replace("            p = os.path.join(ROOT, rel)",
                        "            p = dict(ALL).get(rel, "
                        "os.path.join(ROOT, rel))")
    if 'import alv_tree' not in gout:
        gout = gout.replace(
            "ROOT = os.path.join(os.getcwd(), 'pages', 'templates')",
            "import alv_tree\nROOT = os.path.join(os.getcwd(), 'pages', "
            "'templates')", 1)
    if not CHECK:
        backup(gp)
        write(gp, gout)

    # ---- one control picks its victim by reading PROSE ---------------
    # test_css_order's section 7 plants a collision into a page "no
    # later round has touched" and asserts section 5 catches it. It
    # finds that page by looking for a style tag with `in read(q)` -
    # TEXT, not code.
    #
    # PQ-1 gives six CRS pages a later backup, so they stop qualifying
    # and the search falls through to access_denied.html. That page has
    # NO style block. What it has is a Django comment that says, in so
    # many words, that it carries no style block - and the search
    # matched the sentence. The plant went inside the comment, the
    # parser correctly ignored it, and the control reported "found 0".
    #
    # A CHECK THAT READS TEXT CATCHES PROSE. That is on base's own list
    # of rules that keep being relearned, with twenty-four instances
    # against it, three of them a patcher's own explanation of the
    # thing it was checking. This is the twenty-fifth, and the page was
    # BOASTING about the very property the search was testing for.
    #
    # The repair is not a longer skip list. A page is plantable when it
    # really declares something, so that is what gets asked.
    co = os.path.join(root, 'test_css_order.py')
    OLD = "        if '<style' not in read(q):\n            continue\n"
    NEW = ("        # PQ-1, 10 Oct 2026 - ASK FOR THE PROPERTY THE\n"
           "        # CONTROL NEEDS, which is a page section 5 actually\n"
           "        # SCANS. Two guesses were wrong before this one:\n"
           "        #   `'<style' in read(q)` is TEXT, and matched a\n"
           "        #   Django comment on access_denied.html saying the\n"
           "        #   page carries no style block - it does not, so the\n"
           "        #   plant went into the comment and section 5 rightly\n"
           "        #   saw nothing;\n"
           "        #   then `decls_of(read(q))` alone, which picked\n"
           "        #   components/pdf_viewer.html - real rules, but a\n"
           "        #   STANDALONE page, and collisions() skips those\n"
           "        #   because a page that never sees base cannot\n"
           "        #   override it.\n"
           "        if alv_tree.rel(q).replace(os.sep, '/') in \\\n"
           "                set(alv_tree.standalone()):\n"
           "            continue              # collisions() skips these\n"
           "        if not decls_of(read(q)):\n"
           "            continue              # nothing real to plant beside\n")
    n_ctrl = 0
    if os.path.isfile(co):
        ct = read(co)
        if 'CODE, NOT PROSE' not in ct:
            if ct.count(OLD) != 1:
                raise SystemExit('PQ-1: test_css_order does not pick its '
                                 'victim in the shape this round was '
                                 'measured against')
            if not CHECK:
                backup(co)
                write(co, ct.replace(OLD, NEW, 1))
            n_ctrl += 1

    # ---- the register ------------------------------------------------
    n_reg = 0
    tp = os.path.join(root, 'alv_tree.py')
    tt = read(tp)
    if "'%s':" % GUARD in tt:
        i = tt.index("'%s':" % GUARD)
        j = tt.index('\n', i)
        line = tt[i:j + 1]
        if 'bare max-width' not in line:
            raise SystemExit('PQ-1: the WAITING entry for %s does not read '
                             'as measured: %r' % (GUARD, line[:70]))
        tt2 = tt.replace(line, '', 1)
        tail = "'test_zoom_guards.py',\n"
        if tt2.count(tail) != 1:
            raise SystemExit('PQ-1: the CONVERTED tail is not in alv_tree '
                             'exactly once')
        # AND THIS ROUND'S OWN SUITE. test_crs_print walks the tree
        # too, so test_tree_roots and test_waiting_down hold it to
        # being on exactly one list - the same arrival D-2 made. Both
        # go on CONVERTED: they walk templates through alv_tree and
        # build no root of their own.
        tt2 = tt2.replace(
            tail,
            tail + "    # PQ-1, 10 Oct 2026 - off WAITING: the bare clause\n"
                   "    # it was waiting on is fixed, and it walks the whole\n"
                   "    # tree now.\n    '%s',\n"
                   "    # PQ-1 - and this round's own suite, which walks\n"
                   "    # through alv_tree from the day it was written.\n"
                   "    '%s',\n" % (GUARD, SUITE), 1)
        if not CHECK:
            backup(tp)
            write(tp, tt2)
        n_reg += 1

    wd = os.path.join(root, 'test_waiting_down.py')
    wt = read(wd)
    # 47 -> 49: test_print_queries joins CONVERTED, and so does
    # this round's own suite. A round that changes a number owns every
    # number that counts it, and that includes the ones it adds.
    moves = (('CONVERTED_N = 47', 'CONVERTED_N = 49'),
             ('WAITING_N = 14', 'WAITING_N = 13'),
             ('CEILING = 51', 'CEILING = 50'))
    changed = False
    for old, new in moves:
        if new in wt:
            continue
        if wt.count(old) != 1:
            raise SystemExit('PQ-1: %r is not in test_waiting_down exactly '
                             'once' % old)
        wt = wt.replace(old, new + '   # PQ-1, 10 Oct 2026', 1)
        changed = True
    if changed:
        if not CHECK:
            backup(wd)
            write(wd, wt)
        n_reg += 1

    tr = os.path.join(root, 'test_tree_roots.py')
    rt = read(tr)
    if 'WALKERS_OWN_ROOT_MAX = 50' not in rt:
        if rt.count('WALKERS_OWN_ROOT_MAX = 51') != 1:
            raise SystemExit('PQ-1: the walkers ceiling is not 51 in '
                             'test_tree_roots')
        if not CHECK:
            backup(tr)
            write(tr, rt.replace(
                'WALKERS_OWN_ROOT_MAX = 51',
                'WALKERS_OWN_ROOT_MAX = 50   # PQ-1, 10 Oct 2026 - the '
                'file says\n# this may only FALL, and invites the round '
                'that converts a census to\n# lower it and lock the gain '
                'in. test_print_queries is that census.', 1))
        n_reg += 1

    rp = os.path.join(root, 'alv_rounds.py')
    rr = read(rp)
    if "'%s'" % SUFFIX not in rr:
        tail = "    '.bak_formgrid',\n]\n"
        if rr.count(tail) != 1:
            raise SystemExit('PQ-1: D-4 must be applied and still be last '
                             'in ROUNDS')
        if not CHECK:
            backup(rp)
            write(rp, rr.replace(tail,
                  "    '.bak_formgrid',\n"
                  "    # PQ-1, 10 Oct 2026 - six CRS pages stop printing\n"
                  "    # the phone layout, and the guard can see them.\n"
                  "    '%s',\n]\n" % SUFFIX, 1))
        n_reg += 1

    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        anc = "    'test_form_grid.py'\n)"
        if pt.count(anc) != 1:
            raise SystemExit('PQ-1: the $suites anchor is not in %s exactly '
                             'once - D-4 must be applied and still be last'
                             % PS1)
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(
                anc, "    'test_form_grid.py',\n    '%s'\n)" % SUITE, 1))
        n_reg += 1

    print('')
    print('PQ-1  %d CRS page(s) stop printing the phone layout' % len(plan))
    print('PQ-1  %s walks the whole tree now, not pages/templates' % GUARD)
    print('PQ-1  off alv_tree.WAITING, onto CONVERTED; WAITING_N 14 to 13,')
    print('PQ-1  CONVERTED_N 47 to 49 - the guard and this round\'s own')
    print('PQ-1  suite both walk the tree - and the walkers ceiling 51 to 50')
    print('PQ-1  %d control re-pointed at code instead of prose - it was '
          'picking' % n_ctrl)
    print('PQ-1  a page by a sentence that said the page had no style block')
    print('PQ-1  %d registry file(s) resolved' % n_reg)
    print('PQ-1  base keeps its own 991px clause - the print-leak round')
    print('PQ-1  decided that one hides the sidebar on paper, deliberately')
    print('PQ-1  applied' if CHECK else 'PQ-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
