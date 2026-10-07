# -*- coding: utf-8 -*-
"""PM-1 - Filters and Clear come back on the Passports screen, on a phone.

FOUND BY DW-1 REFUSING TO DO SOMETHING. DW-1 deletes page declarations
that copy base exactly, and it excludes any whose compound base declares
TWICE - once plainly and once inside a media query - because a copy of
the first half is not inert: it renders later than base's override and
defeats it. That exclusion is a defect detector, and this is what it
found.

THE DEFECT. base writes the filter panel's two mobile labels like this:

    .filter-title-text-mobile      { display: none   }   desktop
    .clear-all-text-mobile         { display: none   }
    @media (max-width: 768px) {
        .filter-title-text-mobile  { display: inline }   phone
        .clear-all-text-mobile     { display: inline }
    }

Hidden on a desktop, shown on a phone. passport_management.html copied
the FIRST HALF into its own stylesheet and not the second. Page CSS
renders after base's, so at phone width the page's `none` is the last
rule standing and base's `inline` never applies.

RESULT: on a phone, the Passports filter panel shows the icons with no
words. The button that says Filters says nothing, and the one that says
Clear says nothing. Measured in Chromium at 390px: `none` where base
intends `inline`.

A HALF-COPY, AND THE OTHER THREE PAGES PROVE IT. properties.html,
suppliers.html and tenant.html carry the SAME two classes and are fine -
because they copied BOTH halves. They work by accident of completeness.
Passports copied one line out of two.

WHY DELETE RATHER THAN COMPLETE. Adding the media half to the page would
make four pages carrying a full copy of a base rule, which is four places
for the next drift to start. Deleting the half-copy hands both halves
back to base, which is where they already are.

A STATIC READ SAID NINE PAGES. IT WAS WRONG, AND THE BROWSER SETTLED IT.
Searching the tree for this shape found 16 occurrences on 9 pages. Driven
in Chromium at 1280 and 390, thirteen of those compute exactly what base
intends - the page carries its own media half as well, or its own later
rule. Three differed, and one of those three (.row-actions on
finance_expense) matches base under print too, so it is a deliberate page
override and not this defect.

ONE PAGE. TWO DECLARATIONS. THE OTHER FIFTEEN WERE MY INSTRUMENT.

FILES: pages/templates/passport_management.html (+ .bak_pmlabels),
alv_rounds.py, the PS1 $suites, and the new test_passport_mobile.py.

This is VISIBLE, on a phone, so it goes with its renders.
"""
import collections
import os
import sys

SUFFIX = '.bak_pmlabels'
MARK = 'PM-1, 7 Oct 2026'
SUITE_NAME = 'test_passport_mobile.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_cssrules as R                                   # noqa: E402
import alv_tree as T                                       # noqa: E402

PAGE = T.path_of('passport_management.html')
ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
CHECK = False

CLASSES = ('.filter-title-text-mobile', '.clear-all-text-mobile')
EXPECT_CUTS = 1   # ONE grouped rule carrying BOTH classes


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        with open(p, 'rb') as s, open(b, 'wb') as d:
            d.write(s.read())


def fit(t, b):
    return (b.replace('\r\n', '\n').replace('\n', '\r\n')
            if '\r\n' in t else b.replace('\r\n', '\n'))


def rules_for(path, cls):
    """[(selector, prelude, value, rule_start, rule_end, n_decls)] for every
    rule whose rightmost compound is exactly `cls`."""
    code = T.code_only(read(path))
    out = []
    for a, b in R.style_spans(code):
        bodies = collections.OrderedDict()
        for sel, ba, bb, ra, rb in R.rule_spans(code, a, b):
            bodies.setdefault((ba, bb, ra, rb), []).append(sel)
        for (ba, bb, ra, rb), sels in bodies.items():
            for sel in sels:
                if sel.split(' && ')[-1].strip() != cls:
                    continue
                prel = ' && '.join(sel.split(' && ')[:-1])
                out.append((sel, prel, R.norm(code[ba:bb]), ra, rb,
                            len(sels), ba, bb))
    return out


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    page = read(PAGE)
    rounds = read(ROUNDS)
    ps = read(PS1)
    if MARK in page or "'%s'" % SUFFIX in rounds:
        print('PM-1  already applied')
        return 1 if CHECK else 0

    # --- THE PREMISE: BASE REALLY DOES DECLARE BOTH HALVES --------------
    # If base ever stops showing these on a phone, deleting the page's
    # copy would hide them everywhere rather than fix one page.
    for cls in CLASSES:
        br = rules_for(T.path_of('base.html'), cls)
        plain = [r for r in br if not r[1]]
        media = [r for r in br if r[1]]
        if len(plain) != 1 or 'none' not in plain[0][2]:
            raise SystemExit('PM-1: base does not hide %s plainly (%r) - '
                             'refusing' % (cls, [p[2] for p in plain]))
        if len(media) != 1 or 'inline' not in media[0][2]:
            raise SystemExit('PM-1: base does not SHOW %s inside a media '
                             'query (%r). Deleting the page copy would hide '
                             'it everywhere, not fix one page. Refusing.'
                             % (cls, [m[2] for m in media]))

    # --- AND THE PAGE REALLY DOES CARRY ONLY THE FIRST HALF ------------
    # THE TWO CLASSES SHARE ONE GROUPED RULE on this page:
    #
    #     .filter-title-text-mobile, .clear-all-text-mobile
    #         { display: none; }
    #
    # So this is ONE cut covering two names, not two cuts - and the
    # first version of this gate refused the round for exactly that,
    # which was the right instinct about the wrong rule. A group is
    # safe to cut when EVERY name in it is one this round is removing;
    # it is unsafe when it carries a name base never covered, which is
    # the trap DW-1 hit on customer_invoice_form.
    cuts = {}
    covered = set()
    for cls in CLASSES:
        pr = rules_for(PAGE, cls)
        plain = [r for r in pr if not r[1]]
        media = [r for r in pr if r[1]]
        if media:
            raise SystemExit('PM-1: passport_management ALREADY carries a '
                             'media rule for %s (%r). The half-copy has been '
                             'completed by somebody else and this round has '
                             'nothing to do. Refusing.' % (cls, media[0][2]))
        if len(plain) != 1:
            raise SystemExit('PM-1: passport_management declares %s %d '
                             'time(s) plainly, expected 1' % (cls, len(plain)))
        sel, _prel, val, ra, rb, nsel, ba, bb = plain[0]
        if 'none' not in val:
            raise SystemExit('PM-1: the page rule for %s is %r, not a copy '
                             'of base display none - refusing' % (cls, val))
        if len(val.rstrip(';').split(';')) != 1:
            raise SystemExit('PM-1: the page rule for %s holds more than the '
                             'one declaration (%r) - refusing' % (cls, val))
        cuts[(ra, rb)] = val
        covered.add(cls)

    # every name under every rule being cut must be a name we are removing
    code0 = T.code_only(read(PAGE))
    for a, b in R.style_spans(code0):
        bodies = collections.OrderedDict()
        for sel, ba, bb, ra, rb in R.rule_spans(code0, a, b):
            bodies.setdefault((ra, rb), []).append(sel)
        for (ra, rb), sels in bodies.items():
            if (ra, rb) not in cuts:
                continue
            strays = [s for s in sels
                      if s.split(' && ')[-1].strip() not in CLASSES]
            if strays:
                raise SystemExit('PM-1: the rule being cut also names %r, '
                                 'which base never covered. Cutting it would '
                                 'strip that too. Refusing.' % strays)

    if covered != set(CLASSES):
        raise SystemExit('PM-1: covered %r, expected %r'
                         % (sorted(covered), sorted(CLASSES)))
    cuts = [(ra, rb, '+'.join(CLASSES), v) for (ra, rb), v in cuts.items()]
    if len(cuts) != EXPECT_CUTS:
        raise SystemExit('PM-1: %d rule(s) to cut, expected %d'
                         % (len(cuts), EXPECT_CUTS))

    # --- cut, back to front --------------------------------------------
    out = page
    for ra, rb, cls, val in sorted(cuts, reverse=True):
        a, e = ra, rb
        while a > 0 and out[a - 1] in ' \t':
            a -= 1
        while e < len(out) and out[e] in ' \t':
            e += 1
        if e < len(out) and out[e] == '\n' and a > 0 and out[a - 1] == '\n':
            e += 1
        out = out[:a] + out[e:]

    note = fit(page, """
<!-- PM-1, 7 Oct 2026. This page used to carry
       .filter-title-text-mobile { display: none }
       .clear-all-text-mobile    { display: none }
     which is HALF of what base writes. base hides both plainly and SHOWS
     both inside @media (max-width: 768px). Page CSS renders after base's,
     so the half-copy was the last rule standing on a phone and base's
     media rule never applied: the Filters and Clear buttons showed their
     icons with no words. Both lines are gone; base supplies both halves.
     properties, suppliers and tenant carry the SAME two classes and are
     fine, because they copied BOTH halves - they work by accident of
     completeness. See test_passport_mobile.py. -->
""")
    anchor = fit(page, '{% block content %}')
    if out.count(anchor) != 1:
        raise SystemExit('PM-1: {%% block content %%} matched %d time(s), '
                         'not once' % out.count(anchor))
    out = out.replace(anchor, anchor + note, 1)

    # --- the result must still parse, and must have lost ONLY these ----
    code = T.code_only(out)
    if code.count('{') != code.count('}'):
        raise SystemExit('PM-1: unbalanced braces after the cut')
    for cls in CLASSES:
        if rules_for.__name__ and any(
                sel.split(' && ')[-1].strip() == cls
                for a, b in R.style_spans(code)
                for sel, _ba, _bb, _ra, _rb in R.rule_spans(code, a, b)):
            raise SystemExit('PM-1: %s still has a rule on the page' % cls)
    for keep in ('filter-title-text-mobile', 'clear-all-text-mobile'):
        if keep not in out:
            raise SystemExit('PM-1: the class %s left the MARKUP too - only '
                             'the CSS rule should go' % keep)

    if not CHECK:
        backup(PAGE)
        write(PAGE, out)

        NOTE = """    # PM-1, 7 Oct 2026 - found by DW-1 refusing to cut something.
    # passport_management carried HALF of a base rule: the plain
    # display:none for the two mobile filter labels, and not the
    # @media that shows them on a phone. Page CSS renders later, so
    # the half-copy was the last rule standing and base override
    # never applied - Filters and Clear showed their icons with no
    # words, on that page only. Both lines deleted; base supplies
    # both halves.
    '%s',
""" % SUFFIX
        for anchor in ("    '.bak_deadweight',\n]", "    '.bak_impguard',\n]"):
            if rounds.count(fit(rounds, anchor)) == 1:
                rounds = rounds.replace(
                    fit(rounds, anchor),
                    fit(rounds, anchor[:-2] + NOTE + ']'), 1)
                break
        else:
            raise SystemExit('PM-1: could not find the tail of ROUNDS')
        backup(ROUNDS)
        write(ROUNDS, rounds)

        PS_NOTE = """    # PM-1, 7 Oct 2026 - the two mobile filter labels on Passports.
    # Section 3 drives Chromium at 390 and requires both to compute
    # `inline`, and at 1280 requires both to stay `none`, because the
    # round is a phone fix and must not touch the desktop.
    '%s'
)""" % SUITE_NAME
        for anchor in ("    'test_dead_weight.py'\n)",
                       "    'test_important_base.py'\n)"):
            if ps.count(fit(ps, anchor)) == 1:
                ps = ps.replace(fit(ps, anchor),
                                fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
                break
        else:
            raise SystemExit('PM-1: could not find the tail of $suites')
        backup(PS1)
        write(PS1, ps)

        # ==============================================================
        # THE TWO SUITES THIS ROUND MOVED, AND IT OWNS BOTH.
        # ==============================================================

        # 1. test_ingredient_filter pins the FOUR pages that still define
        #    the label swaps locally instead of leaving them to base.
        #    Passports was one of them and is not any more, so the list
        #    is three. The claim is unchanged and better: it is a record
        #    of who has not adopted base yet, and one page just did.
        IF = os.path.join(ROOT, 'test_ingredient_filter.py')
        OLD_LIST = ("LOCAL_LABELS = ('passport_management.html', "
                    "'properties.html',\n                'suppliers.html', "
                    "'tenant.html')")
        NEW_LIST = ("# PM-1, 7 Oct 2026: passport_management leaves this "
                    "list. It carried\n"
                    "# HALF of base rule - the plain display:none and not "
                    "the media query\n"
                    "# that shows the labels on a phone - so on a phone "
                    "NEITHER label\n"
                    "# showed. Both lines deleted; base owns both halves "
                    "there now.\n"
                    "LOCAL_LABELS = ('properties.html',\n"
                    "                'suppliers.html', 'tenant.html')")
        src = read(IF)
        if src.count(fit(src, OLD_LIST)) != 1:
            raise SystemExit('PM-1: LOCAL_LABELS in test_ingredient_filter.py '
                             'matched %d time(s), not once'
                             % src.count(fit(src, OLD_LIST)))
        backup(IF)
        write(IF, src.replace(fit(src, OLD_LIST), fit(src, NEW_LIST), 1))

        # 2. test_dead_weight READS THE PAGE LIVE, AND IT MUST NOT.
        #
        #    THIS IS THE FIFTH TIME. test_tab_right_edge, test_table_admin,
        #    test_celebration_az and test_ei_modal were each caught reading
        #    a page as it is NOW rather than as their own round left it.
        #    DW-1 section 6 asserts that passport_management STILL carries
        #    display:none for those two classes - which was true when DW-1
        #    ran, is the whole reason DW-1 refused to cut them, and stops
        #    being true the moment PM-1 does cut them.
        #
        #    Bumping the assertion would turn a statement about DW-1 into a
        #    statement about whatever ran last. The fix is always the same:
        #    read at that round's own scope.
        DW = os.path.join(ROOT, 'test_dead_weight.py')
        src = read(DW)
        OLD_IMPORT = "import apply_dead_weight as D                              # noqa: E402"
        NEW_IMPORT = ("import apply_dead_weight as D                              "
                      "# noqa: E402\n"
                      "from alv_rounds import as_left_by                          "
                      "# noqa: E402\n"
                      "\n"
                      "\n"
                      "def as_dw1_left(p):\n"
                      "    \"\"\"The page as DW-1 LEFT it, not as it is today.\n"
                      "\n"
                      "    PM-1, 7 Oct 2026. Sections 6 and 7 read this page\n"
                      "    live and PM-1 then cut two more rules out of it -\n"
                      "    rules DW-1 deliberately refused, which is how PM-1\n"
                      "    found the defect in the first place. A round can\n"
                      "    only speak for its own work.\n"
                      "    \"\"\"\n"
                      "    return as_left_by(p, SUFFIX, read)")
        if src.count(fit(src, OLD_IMPORT)) != 1:
            raise SystemExit('PM-1: the import block in test_dead_weight.py '
                             'matched %d time(s), not once'
                             % src.count(fit(src, OLD_IMPORT)))
        src = src.replace(fit(src, OLD_IMPORT), fit(src, NEW_IMPORT), 1)

        # every read(p) of a TOUCHED page becomes now(p)
        for old, new2 in (
                ("    now = T.code_only(read(p))",
                 "    now = T.code_only(now(p))"),
                ("    was = T.code_only(read(p + SUFFIX))\n"
                 "    now = T.code_only(read(p))",
                 "    was = T.code_only(read(p + SUFFIX))\n"
                 "    now = T.code_only(now(p))"),
        ):
            pass
        src = src.replace(fit(src, "T.code_only(read(p))"),
                          fit(src, "T.code_only(as_dw1_left(p))"))
        src = src.replace(fit(src, "css_of(read(p))"),
                          fit(src, "css_of(as_dw1_left(p))"))
        src = src.replace(fit(src, "    code = T.code_only(read(pm))"),
                          fit(src, "    code = T.code_only(as_dw1_left(pm))"))
        if 'T.code_only(read(p))' in src or 'css_of(read(p))' in src:
            raise SystemExit('PM-1: a live read survives in test_dead_weight')
        import ast as _ast
        try:
            _ast.parse(src)
        except SyntaxError as e:
            raise SystemExit('PM-1: test_dead_weight.py would not parse - %s'
                             % e)
        backup(DW)
        write(DW, src)
        print('PM-1  test_ingredient_filter: LOCAL_LABELS 4 -> 3')
        print('PM-1  test_dead_weight: reads at DW-1 scope, not live')

    print('PM-1  the half-copied rule deleted (one rule, both classes)')
    print('PM-1  Filters and Clear now show on a phone, as base intends')
    if CHECK:
        print('PM-1  NOT APPLIED')
        return 1
    print('PM-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
