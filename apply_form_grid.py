# -*- coding: utf-8 -*-
"""apply_form_grid.py - Section D round D-4, 10 Oct 2026.

TWELVE PAGES WROTE THE SAME COMPONENT. BASE SAYS IT ONCE.

D-4 was recorded as "should base grow a form grid". Measured, twelve
pages have already grown one, and they agree character for character:

    11 x  display: grid; grid-template-columns: 1fr 1fr; gap: 18px 22px;
     8 x  @media ... grid-template-columns: 1fr; gap: 14px;
     4 x  .form-group-full  grid-column: 1 / -1;

This is the case base's own standards block closes on - that is how
the system acquired five colours of one component and thirty local
copies of one action row.

NOTHING RENDERS DIFFERENTLY, WITH ONE EXCEPTION, AND IT IS SHOWN.
Twelve pages use the class and twelve declare it: a clean one to one,
no page relying on a rule it does not have. So lifting the rule into
base and deleting the copies leaves every page where it was - except
crs/submission_detail.html, which writes repeat(2, 1fr) with a 14px
gap. The columns are the same thing spelled differently; the gap is
genuinely tighter, and that page adopts base's 18px/22px on his call,
from a render.

WHAT THIS ROUND IS NOT
----------------------
IT DOES NOT UNBLOCK IN-2, and the outstanding list said it would.
customer_invoice_form.html does not use .form-grid at all; its
sideways scroll comes from a table, .lines-table with a 720px minimum
width. A form grid cannot touch it. IN-2 needs its own look.

IT DOES NOT TOUCH THE REST OF THE FORM FAMILY. 44 pages carry 111
rules there, including a real disagreement about .form-card's phone
radius (12 say 10px, 6 say 8px) and four pages setting a label weight
of 500 against the house decision of bold, settled 9 Sep. Those are
named in the doc and left for their own rounds. This round lifts one
component, not a family.

A DEFECT FOUND ON THE WAY, PARTLY FIXED BY ACCIDENT
---------------------------------------------------
Eight CRS pages carry a phone query with no `screen` keyword. A4
portrait is about 718 CSS px, so those rules fire ON PAPER - printing
a CRS page gives the phone layout. The house rule has said `screen`
since 21 Sep and test_print_queries enforces it, but that suite walks
pages/templates only and has never seen crs/templates.

Two of the eight hold nothing but the grid rule, so removing the rule
empties the block and this round takes it away. That is 2 of 8 closed
as a side effect, not a fix - the other six need their own round, and
the suite needs its root widened. Said out loud because a side effect
nobody writes down is how a list starts lying.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree as T                                          # noqa: E402

SUFFIX = '.bak_formgrid'
MARK = 'D-4, 10 Oct 2026'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_form_grid.py'
ME = 'apply_form_grid.py'
CHECK = False

N_PAGES = 12
N_DESK = 12          # 11 agreeing + submission_detail's repeat(2, 1fr)
N_PHONE = 12
N_FULL = 4
N_EMPTIED = 2        # media blocks that held nothing else

BASE_ANCHOR = '.form-group { margin-bottom: 16px; }'
BASE_RULES = """/* D-4, 10 Oct 2026 - THE TWO-COLUMN FIELD ROW, said once.
   Twelve pages had written this out and eleven of them agreed
   character for character, down to the 18px/22px gap. The twelfth,
   crs/submission_detail, spelled the columns repeat(2, 1fr) and used
   a 14px gap; it adopts these values here, which is the only visible
   change in the round and was taken from a render.
   .form-group-full is the escape hatch the four CRS forms already
   used: one field spanning both columns. */
.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px 22px;
}

.form-group-full { grid-column: 1 / -1; }

/* THE KEYWORD IS NOT OPTIONAL. A4 portrait is about 718 CSS px, so a
   bare max-width query fires on paper and prints the phone layout.
   Eight CRS pages do exactly that today; this one does not. */
@media screen and (max-width: 768px) {
    .form-grid { grid-template-columns: 1fr; gap: 14px; }
}

"""

STD_OLD = ("Rows are\n      still Bootstrap's grid and base does not "
           "touch them.")
STD_NEW = (
    "The two-column field row is\n"
    "      base's too since D-4, 10 Oct: .form-grid, collapsing to one\n"
    "      column on a phone, with .form-group-full for a field that\n"
    "      spans both. Twelve pages had written it out and eleven agreed\n"
    "      exactly; the twelfth adopted the majority gap. Bootstrap's own\n"
    "      row and column classes are untouched and remain the way to lay\n"
    "      out anything that is not a pair of fields.")

DESK = re.compile(r'\.form-grid\s*\{[^}]*display:\s*grid[^}]*\}')
PHONE = re.compile(r'\.form-grid\s*\{(?![^}]*display:\s*grid)[^}]*\}')
FULL = re.compile(r'\.form-group-full\s*\{[^}]*\}')


def read(p):
    return open(p, encoding='utf-8', newline='').read()


def write(p, t):
    open(p, 'w', encoding='utf-8', newline='').write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def empty_media_spans(text):
    """(start, end) for every @media block whose body holds no rule.

    AFTER THE RULE COMES OUT, two pages are left with an empty phone
    block. An empty block is not a bug a browser minds, but it is a
    page saying it has something to say on a phone when it does not.
    """
    out = []
    for m in re.finditer(r'@media[^{]*\{', text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
            i += 1
        if not text[m.end():i - 1].strip():
            out.append((m.start(), i))
    return out


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    bp = T.path_of('base.html')
    if MARK in read(bp):
        print('D-4  already applied')
        return 0

    # ---- survey first ------------------------------------------------
    plan = []
    n_desk = n_phone = n_full = 0
    for p in sorted(T.templates()):
        if os.path.abspath(p) == os.path.abspath(bp):
            continue
        raw = read(p)
        code = T.code_only_js(raw)
        d = [m.span() for m in DESK.finditer(code)]
        f = [m.span() for m in FULL.finditer(code)]
        ph = [m.span() for m in PHONE.finditer(code)]
        if not (d or f or ph):
            continue
        n_desk += len(d)
        n_phone += len(ph)
        n_full += len(f)
        plan.append((p, T.rel(p), raw, d + ph + f))

    if len(plan) != N_PAGES:
        raise SystemExit('D-4: found the grid on %d page(s), measured at %d'
                         % (len(plan), N_PAGES))
    if (n_desk, n_phone, n_full) != (N_DESK, N_PHONE, N_FULL):
        raise SystemExit(
            'D-4: found %d desktop, %d phone, %d full-width rule(s); '
            'measured at %d, %d, %d'
            % (n_desk, n_phone, n_full, N_DESK, N_PHONE, N_FULL))

    # EVERY USER MUST BE A DECLARER. If a page used the class without a
    # rule it would start laying out in columns the moment base owned
    # it - a visible change nobody asked for. Measured at zero.
    users = set()
    for p in sorted(T.templates()):
        if re.search(r'class="[^"]*\bform-grid\b', read(p)):
            users.add(T.rel(p))
    orphan = sorted(users - {rel for _p, rel, _r, _s in plan})
    if orphan:
        raise SystemExit('D-4: %d page(s) use form-grid and declare no '
                         'rule, so base taking it over would CHANGE them: '
                         '%s' % (len(orphan), orphan))

    # ---- write the pages ---------------------------------------------
    emptied = 0
    for p, rel, raw, spans in plan:
        out = raw
        for a, b in sorted(spans, reverse=True):
            out = out[:a] + out[b:]
        before = len(empty_media_spans(T.code_only_js(raw)))
        gaps = empty_media_spans(T.code_only_js(out))
        for a, b in sorted(gaps, reverse=True):
            out = out[:a] + out[b:]
        emptied += len(gaps) - before
        out = re.sub(r'\n[ \t]*\n[ \t]*\n+', '\n\n', out)
        if not CHECK:
            backup(p)
            write(p, out)

    if emptied != N_EMPTIED:
        raise SystemExit('D-4: %d media block(s) were left empty; measured '
                         'at %d' % (emptied, N_EMPTIED))

    # ---- base gains the component ------------------------------------
    bt = read(bp)
    if bt.count(BASE_ANCHOR) != 1:
        raise SystemExit('D-4: the .form-group anchor is not in base.html '
                         'exactly once')
    if bt.count(STD_OLD) != 1:
        raise SystemExit('D-4: the standards sentence about Bootstrap rows '
                         'is not in base.html exactly once - the block has '
                         'moved since this round was written')
    out = bt.replace(BASE_ANCHOR, BASE_RULES + BASE_ANCHOR, 1)
    # UPDATE THE BLOCK IN THE SAME ROUND - base's own rule, section 6.
    # And NO BRACES in that document: a suite once read a declaration
    # written out in prose as a component's real colour and it cost a
    # push. Class names only.
    out = out.replace(STD_OLD, STD_NEW, 1)
    if '{' in STD_NEW or '}' in STD_NEW:
        raise SystemExit('D-4: the standards amendment contains a brace')

    # verify, THEN write
    if MARK not in out:
        raise SystemExit('D-4: the round note did not land in base')
    if not CHECK:
        backup(bp)
        write(bp, out)

    # ---- three CRS suites record a state this round changes -----------
    # Each asserts, of its own page, that .form-grid is "a house
    # convention base has not hoisted yet", and counts how many other
    # pages write it out. D-4 hoists it, so the count collapses and the
    # sentence becomes false.
    #
    # THE CLAIM IS NOT THE COUNT. What those checks are about is that
    # the page follows the house rather than inventing something, and
    # after this round base declaring it is a STRONGER form of exactly
    # that claim. So each one is narrowed to it - which is the opposite
    # of re-pointing a guard at whatever the new string happens to be.
    # B-4's rule: a pinned count moves when a later round owns part of
    # it; a pinned decision does not. This round owns the count.
    #
    # The check immediately after it - that the page spells the grid
    # the way finance_expense_add does - is deliberately LEFT ALONE. It
    # reads the page as that round left it, through as_left_by, so it
    # still passes and still means what it meant.
    OLD = (
        "grids = [alv_tree.rel(p) for p in alv_tree.templates()\n"
        "         if 'form-card' in read(p)\n"
        "         and re.search(r'\\.form-(?:grid|row-2)\\s*\\{"
        "[^}]*grid-template-columns',\n"
        "                       read(p))]\n"
        "ok(len(grids) >= 9,\n"
        "   '  .form-grid is a house convention base has not hoisted yet "
        "- %d other '\n"
        "   'form pages already do exactly this' % len(grids), grids[:6])")
    NEW = (
        "# D-4, 10 Oct 2026 - base HAS hoisted it now, so counting the\n"
        "# pages that write it out is counting the wrong thing. The\n"
        "# claim was always that this page follows the house; base\n"
        "# declaring the component is a stronger way of saying so.\n"
        "_bg = read(alv_tree.path_of('base.html'))\n"
        "ok(re.search(r'\\.form-grid\\s*\\{[^}]*grid-template-columns',\n"
        "             _bg) is not None,\n"
        "   '  .form-grid is the house component, declared in base since "
        "D-4 '\n"
        "   '- this page uses it rather than inventing one')")
    n_suite = 0
    for s in ('test_crs_country_form.py', 'test_crs_fi_form.py',
              'test_crs_submission_start.py'):
        sp = os.path.join(root, s)
        if not os.path.isfile(sp):
            continue
        st = read(sp)
        if 'base HAS hoisted it now' in st:
            continue
        if st.count(OLD) != 1:
            raise SystemExit('D-4: %s does not carry the hoist check in the '
                             'shape this round was measured against' % s)
        if not CHECK:
            backup(sp)
            write(sp, st.replace(OLD, NEW, 1))
        n_suite += 1

    # ---- registration --------------------------------------------------
    n_reg = 0
    rp = os.path.join(root, 'alv_rounds.py')
    rt = read(rp)
    if "'%s'" % SUFFIX not in rt:
        tail = "    '.bak_radtoken',\n]\n"
        if rt.count(tail) != 1:
            raise SystemExit('D-4: D-12 must be applied and still be last '
                             'in ROUNDS')
        if not CHECK:
            backup(rp)
            write(rp, rt.replace(tail,
                  "    '.bak_radtoken',\n"
                  "    # D-4, 10 Oct 2026 - base grows the two-column\n"
                  "    # field row that twelve pages had written out.\n"
                  "    '%s',\n]\n" % SUFFIX, 1))
        n_reg += 1
    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        anc = "    'test_bar_height.py'\n)"
        if pt.count(anc) != 1:
            raise SystemExit('D-4: the $suites anchor is not in %s exactly '
                             'once - D-1 must be applied and still be last'
                             % PS1)
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(
                anc, "    'test_bar_height.py',\n    '%s'\n)" % SUITE, 1))
        n_reg += 1

    print('')
    print('D-4  base now declares .form-grid and .form-group-full')
    print('D-4  %d rule(s) removed from %d page(s): %d desktop, %d phone, '
          '%d full-width' % (n_desk + n_phone + n_full, len(plan),
                             n_desk, n_phone, n_full))
    print('D-4  %d phone block(s) held nothing else and went with them '
          '- which closes 2 of the 8 CRS pages whose phone query has no '
          'screen keyword' % emptied)
    print('D-4  %d CRS suite(s) narrowed from counting the pages that '
          'wrote it' % n_suite)
    print('D-4  out, to asserting base declares it - the claim they were '
          'always making')
    print('D-4  the standards block says so too, in the same round')
    print('D-4  %d registry file(s) resolved' % n_reg)
    print('D-4  ONE page changes visibly: crs/submission_detail adopts the')
    print('D-4  majority gap. Everything else renders exactly as before.')
    print('D-4  applied' if CHECK else 'D-4  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
