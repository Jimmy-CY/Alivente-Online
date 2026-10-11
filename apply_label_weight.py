# -*- coding: utf-8 -*-
"""apply_label_weight.py - round LB-1, 10 Oct 2026.

ONE WEIGHT FOR A FIELD LABEL, AND ONE MECHANISM THAT CARRIES IT.

The standard was settled on 9 Sep: a field label is bold, and the bold
comes from the MARKUP - `label > strong` - not from a rule somebody has
to remember. base deliberately sets no font-weight on `.form-group
label`, and that is correct: 67 labels in the corpus wrap only PART of
themselves, so the name is bold and the hint beside it is not.

    <label><strong>Email CC</strong> (optional)</label>

A weight on the label itself would flatten every one of those.

MEASURED, THE SYSTEM WEARS FOUR WEIGHTS FOR ONE THING
-----------------------------------------------------
    400   a plain field name, no page rule
    600   a plain field name under a page rule
    700   the house majority - <strong>, no page rule
    900   <strong> UNDER a page rule

THE 900 IS THE PART NOBODY CHOSE. `<strong>` carries the browser's
`font-weight: bolder`, which is RELATIVE: bolder of 400 computes to 700,
and bolder of 600 computes to 900. Eighteen pages set 600 on the label
for the look of it and pushed their own `<strong>` two steps past the
house. Not one of them asked for 900.

WHAT THIS ROUND DOES
--------------------
1. base pins `<strong>` inside a field label to an ABSOLUTE 700. The
   relativity is the bug, so the fix is to stop being relative. After
   this, a page rule cannot produce a 900 label however hard it tries.
2. The 24 plain field labels on the four CRS form pages gain `<strong>`,
   in base's own shape: the NAME bold, the asterisk left outside in its
   `span.alv-req`, which is what 145 labels in the corpus already do.
3. The 22 page-local `.form-group label` weight rules come out. Every
   one of them holds a font-weight AND NOTHING ELSE, so what is removed
   is the whole rule, not a line out of the middle of one.
4. test_label_bold.py is widened to walk every root and taught to see a
   Django-rendered control, and comes off alv_tree.WAITING.

THE CRS FORMS, AND WHY 4 WAS THE WRONG NUMBER
---------------------------------------------
test_label_bold decides something is a field by finding `form-control`
on the control beside it. On the CRS forms the control is `{{ form.x }}`
and the class lives in crs/forms.py - `_INPUT = {"class":
"form-control"}` reaching 28 fields. So the suite could see 4 of the 24.
D-2's lesson, one module along: THE TEMPLATE IS NOT THE PAGE.

Bolding only the 4 it could see would have left country_form and fi_form
half bold, which is worse than either end state, so the round takes the
module and the suite learns to look.

WHAT IS DELIBERATELY NOT TOUCHED
--------------------------------
THE RECIPE SIDE. 55 plain field labels live there. Section 2.K settled
that the recipe templates are reported and never failed, because no
round has swept them and failing on them would be failing on work nobody
has agreed to do. That decision is older than this round and survives it.

THE 67 PART-WRAPPED LABELS, for the reason at the top.

THE THREE PAGES test_label_bold ALREADY NAMES in NOT_SWEPT - three
labels JavaScript rewrites, a size hint in a <small>, and a sentence of
instruction that is not a field name at all.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_lblwt'
SUITE = 'test_label_weight.py'
HELD = 'test_label_bold.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
X0 = 'test_tree_roots.py'
WD = 'test_waiting_down.py'
PQ = 'test_crs_print.py'
ROUNDS = 'alv_rounds.py'
CHECK = False

# base's one new rule. ABSOLUTE, not `bolder`, and that is the whole
# point of it - see the header.
GUARD = (
    '\n/* LB-1, 10 Oct 2026 - THE BOLD IS ABSOLUTE, NOT RELATIVE.\n'
    '   <strong> carries the browser\'s font-weight: bolder, and bolder is\n'
    '   measured FROM THE LABEL: 400 gives 700, but 600 gives 900. Eighteen\n'
    '   pages set 600 on the label and pushed their own labels two steps\n'
    '   past the house without asking for it. Pinning the value here ends\n'
    '   that class of accident - and it is on the strong rather than on the\n'
    '   label because 67 labels in the corpus bold only their NAME and keep\n'
    '   a hint beside it in normal weight. A weight on the label would\n'
    '   flatten all 67. */\n'
    '.form-group label strong,\n'
    '.form-group label b { font-weight: 700; }\n')

BASE_ANCHOR = ('.form-group label {\n'
               '    display: block;\n'
               '    color: var(--alv-ink);\n'
               '    font-size: 14px;\n'
               '    margin-bottom: 6px;\n'
               '}\n')

# The 24, page by page, as the templates spell them. Each entry is the
# EXACT inner text of the label today; the patcher refuses if a page does
# not hold its own list exactly once each.
CRS = {
    'crs/country_form.html': [
        'Country Code <span class="alv-req">*</span>',
        'Country Name <span class="alv-req">*</span>',
        'OECD Version <span class="alv-req">*</span>',
        'Default Currency <span class="alv-req">*</span>',
        'Receiving Country Strategy <span class="alv-req">*</span>',
        'Message Ref ID Template',
        'FI Doc Ref ID Template',
        'Account Doc Ref ID Template',
        'Output Filename Template',
        'TIN Regex',
    ],
    'crs/fi_form.html': [
        'Name <span class="alv-req">*</span>',
        'Name Type <span class="alv-req">*</span>',
        'Residence Country Code <span class="alv-req">*</span>',
        'Address Country Code <span class="alv-req">*</span>',
        'Address Type <span class="alv-req">*</span>',
        'Address <span class="alv-req">*</span>',
        'Contact Details',
    ],
    'crs/submission_detail.html': [
        'Submission notes (optional \u2014 reference number, portal receipt,'
        ' etc.)',
        'Acknowledgement notes (optional)',
        'Rejection reason <span class="alv-req">*</span>',
    ],
    'crs/submission_start.html': [
        'Reporting FI <span class="alv-req">*</span>',
        'Country <span class="alv-req">*</span>',
        'Reporting Year <span class="alv-req">*</span>',
        'Sending Company IN \u2014 TIN <span class="alv-req">*</span>',
    ],
}

# THE TWO THAT ARE NOT WHOLE NAMES. Both are one of the 67: a field name
# with a parenthesised hint after it. Bolding the whole string would make
# the hint shout, so only the name is wrapped - which is exactly what the
# other 65 already do.
PART = {
    'Submission notes (optional \u2014 reference number, portal receipt,'
    ' etc.)': 'Submission notes',
    'Acknowledgement notes (optional)': 'Acknowledgement notes',
}

# The 22 rules. Each is a WHOLE rule: selector, brace, one font-weight,
# brace. Nothing else is inside any of them - checked, not assumed.
WEIGHTED = (
    'create_meal_plan.html', 'customer_form.html',
    'customer_invoice_form.html', 'finance_expense_add.html',
    'finance_expense_edit.html', 'finance_expense_line_types_add.html',
    'finance_expense_line_types_edit.html', 'finance_expense_types_add.html',
    'finance_expense_types_edit.html', 'finance_revenue_add.html',
    'finance_revenue_edit.html', 'finance_revenue_line_types_add.html',
    'finance_revenue_line_types_edit.html', 'finance_revenue_types_add.html',
    'finance_revenue_types_edit.html', 'my_profile.html',
    'notification_settings.html', 'personal_notification_settings.html',
    'user_add.html', 'user_edit.html', 'workspace_add.html',
    'workspace_edit.html',
)

RULE = re.compile(r'[ \t]*\.form-group\s+label\s*\{([^{}]*)\}\n?')
REQ = re.compile(r'<span\s+class="alv-req">\*</span>\s*$')
N_CRS = 24
N_WEIGHTED = 22


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
    raise SystemExit('LB-1 REFUSED: %s' % msg)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    sys.path.insert(0, root)
    import alv_tree as T

    base_p = T.path_of('base.html')

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED, ASKED BEFORE ANYTHING IS SURVEYED. A patcher that
    # surveys first finds nothing left to do on its second run and
    # refuses - which is what D-12 did, once, on his machine.
    if '.form-group label strong' in read(base_p):
        print('LB-1  already applied')
        return 0

    if not os.path.isfile(SUITE):
        refuse('%s is not on disk - the suite ships with the round' % SUITE)

    # ---------------------------------------------------------------- 1
    b = read(base_p)
    if b.count(BASE_ANCHOR) != 1:
        refuse('base.html does not hold the .form-group label rule exactly '
               'once in the shape this round reads')
    nb = b.replace(BASE_ANCHOR, BASE_ANCHOR + GUARD, 1)

    # ---------------------------------------------------------------- 2
    crs_edits = {}
    n_crs = 0
    for rel, labels in CRS.items():
        p = T.path_of(rel)
        t = read(p)
        for inner in labels:
            pat = re.compile(r'(<label\b[^>]*>)\s*' + re.escape(inner)
                             + r'\s*(</label>)')
            found = pat.findall(t)
            if len(found) != 1:
                refuse('%s: expected exactly one label reading %r, found %d'
                       % (rel, inner[:40], len(found)))
            # THE ASTERISK STAYS OUTSIDE THE STRONG. base's own note
            # spells the shape out - `label > strong` is the field NAME
            # and `span.alv-req` is the asterisk - and 145 labels in the
            # corpus already write it that way against 12 that do not.
            # Wrapping the whole inner text would have bolted the star
            # inside and made these four pages the exception.
            name = PART.get(inner)
            if name is None:
                m_req = REQ.search(inner)
                name = inner[:m_req.start()].rstrip() if m_req else inner
            rest = inner[len(name):]
            new = ('\\1<strong>' + name.replace('\\', '\\\\')
                   + '</strong>' + rest.replace('\\', '\\\\') + '\\2')
            t = pat.sub(lambda m, n=new: m.expand(n), t, count=1)
            n_crs += 1
        crs_edits[p] = t
    if n_crs != N_CRS:
        refuse('wrapped %d CRS label(s), expected %d' % (n_crs, N_CRS))

    # ---------------------------------------------------------------- 3
    wt_edits = {}
    n_wt = 0
    for rel in WEIGHTED:
        p = T.path_of(rel)
        t = read(p)
        ms = [m for m in RULE.finditer(t)]
        hit = [m for m in ms if 'font-weight' in m.group(1)]
        if len(hit) != 1:
            refuse('%s: expected exactly one .form-group label rule carrying '
                   'a font-weight, found %d' % (rel, len(hit)))
        body = hit[0].group(1)
        # THE RULE MUST HOLD NOTHING BUT THE WEIGHT. If a later round has
        # put something else in it, removing the rule would take that too,
        # so refuse rather than guess.
        left = re.sub(r'font-weight\s*:\s*[^;]+;?', '', body).strip()
        if left:
            refuse('%s: the rule holds more than the weight (%r) - this '
                   'round removes whole rules only' % (rel, left[:40]))
        wt_edits[p] = t[:hit[0].start()] + t[hit[0].end():]
        n_wt += 1
    if n_wt != N_WEIGHTED:
        refuse('emptied %d rule(s), expected %d' % (n_wt, N_WEIGHTED))

    # ---------------------------------------------------------------- 4
    held = read(HELD)
    if 'alv_tree' in held:
        refuse('%s already reads alv_tree - widened by someone else' % HELD)
    narrow = ("def templates():\n"
              "    out = []\n"
              "    for dirpath, _d, names in os.walk(T):\n")
    if held.count(narrow) != 1:
        refuse('%s does not hold its narrow walk in the shape this round '
               'reads' % HELD)
    wide = (
        "def templates():\n"
        "    # LB-1, 10 Oct 2026 - WIDENED. This walked pages/templates\n"
        "    # alone, and the CRS module is a root of its own at\n"
        "    # crs/templates/crs. Eight files, four of them forms, were\n"
        "    # outside every count this suite printed.\n"
        "    out = []\n"
        "    for dirpath, _d, names in alv_tree.walk3():\n")
    nheld = held.replace(narrow, wide, 1)

    imp = "import sys\n"
    if nheld.count(imp) < 1:
        refuse('%s has no import block this round recognises' % HELD)
    nheld = nheld.replace(imp, imp + "\nimport alv_tree\n", 1)

    old_rel = ("def rel_of(p):\n"
               "    return os.path.relpath(p, T).replace(os.sep, '/')\n")
    if nheld.count(old_rel) != 1:
        refuse('%s does not hold rel_of in the shape this round reads' % HELD)
    nheld = nheld.replace(
        old_rel,
        "def rel_of(p):\n"
        "    # LB-1 - alv_tree knows which root a path came from; relpath\n"
        "    # against one of them turns every CRS file into ../../crs/...\n"
        "    return alv_tree.rel(p)\n", 1)

    # control_of learns to see a Django-rendered control. See the header.
    old_ctl = "    after = scan[m.end():m.end() + 400]\n"
    if nheld.count(old_ctl) != 1:
        refuse('%s does not hold control_of in the shape this round reads'
               % HELD)
    nheld = nheld.replace(
        old_ctl,
        "    after = scan[m.end():m.end() + 400]\n"
        "    # LB-1 - A TEMPLATE IS NOT THE PAGE. On the CRS forms the\n"
        "    # control is {{ form.x }} and its class is set in\n"
        "    # crs/forms.py, so reading the markup alone found four of\n"
        "    # twenty-four field labels and called the other twenty\n"
        "    # something else. widget_class() asks the form.\n"
        "    dj = re.search(r'\\{\\{\\s*form\\.(\\w+)\\s*\\}\\}', after)\n"
        "    _l = re.search(r'<label\\b', after)\n"
        "    _n = re.search(CTRL, after)\n"
        "    if dj and (not _l or dj.start() < _l.start()) \\\n"
        "            and (not _n or dj.start() < _n.start()):\n"
        "        return '<input class=\"%s\">' % widget_class(dj.group(1))\n",
        1)


    # Section 3 reports "page-local CSS rules that also bold a label".
    # base is not a page - it is where such a rule is SUPPOSED to live -
    # and this round puts one there, so without this the round would
    # have added itself to a list of things to tidy up.
    old_rep = ("weighted = []\n"
               "for p in templates():\n"
               "    rel = rel_of(p)\n"
               "    if is_recipe(rel):\n"
               "        continue\n")
    if nheld.count(old_rep) != 1:
        refuse('%s does not hold its section 3 census where this round '
               'expects it' % HELD)
    nheld = nheld.replace(
        old_rep,
        "weighted = []\n"
        "for p in templates():\n"
        "    rel = rel_of(p)\n"
        "    # LB-1 - and not base, which is not a page. A label rule in\n"
        "    # base is the house saying it once, which is the opposite of\n"
        "    # the thing this report is for.\n"
        "    if is_recipe(rel) or rel == 'base.html':\n"
        "        continue\n", 1)

    old_fields = "def fields_of(text):\n"
    if nheld.count(old_fields) != 1:
        refuse('%s does not hold fields_of where this round expects it'
               % HELD)
    helper = (
        "_WIDGETS = None\n"
        "\n"
        "\n"
        "def widget_class(field):\n"
        "    \"\"\"The class a Django widget really renders with.\n"
        "\n"
        "    Read from the form classes, not guessed from the template.\n"
        "    Returns '' when the form cannot be loaded at all, which makes\n"
        "    the label fall out of the census rather than into it - a\n"
        "    missing answer must never read as a passing one.\n"
        "    \"\"\"\n"
        "    global _WIDGETS\n"
        "    if _WIDGETS is None:\n"
        "        _WIDGETS = {}\n"
        "        try:\n"
        "            import django\n"
        "            os.environ.setdefault('DJANGO_SETTINGS_MODULE',\n"
        "                                  'mysite.settings')\n"
        "            django.setup()\n"
        "            from crs import forms as _f\n"
        "            for _n in dir(_f):\n"
        "                _o = getattr(_f, _n)\n"
        "                _bf = getattr(_o, 'base_fields', None)\n"
        "                if not isinstance(_o, type) or not _bf:\n"
        "                    continue\n"
        "                for _k, _v in _bf.items():\n"
        "                    _c = str(_v.widget.attrs.get('class', ''))\n"
        "                    if _c:\n"
        "                        _WIDGETS[_k] = _c\n"
        "        except Exception:\n"
        "            _WIDGETS = {}\n"
        "    return _WIDGETS.get(field, '')\n"
        "\n"
        "\n")
    nheld = nheld.replace(old_fields, helper + old_fields, 1)

    # A ROUND THAT CHANGES A NUMBER OWNS EVERY NUMBER THAT COUNTS IT.
    # Widening test_label_bold moves three counters that THREE other
    # suites pin, and leaves one dormant narrow lookup behind in the
    # suite itself - the exact pattern X0 closed: resolving a label
    # against the one root the file happened to know about.
    #
    # The third is PQ-1's own suite, which cross-checks the other two by
    # literal. That one is not re-pinned, it is REWRITTEN: its claim was
    # never "the number is 49", it was "test_waiting_down's constants are
    # not stale". Asserting them against the live register says exactly
    # that and never needs editing again. B-4's rule - a pinned COUNT
    # moves when a later round owns part of it; a pinned DECISION does
    # not - and this one turned out to be neither: it was a pinned
    # CONSISTENCY, written as a count.
    old_base = "BASE = os.path.join(T, 'base.html')\n"
    if nheld.count(old_base) != 1:
        refuse('%s does not resolve base.html where this round expects'
               % HELD)
    nheld = nheld.replace(
        old_base,
        "# LB-1 - through alv_tree, not through the one root this file\n"
        "# used to know about. base.html happens to live under\n"
        "# pages/templates, so the old join worked - which is exactly\n"
        "# what made it a DORMANT lookup rather than a broken one.\n"
        "BASE = alv_tree.path_of('base.html')\n", 1)

    x0 = read(X0)
    old_ceiling = 'WALKERS_OWN_ROOT_MAX = 50   # PQ-1, 10 Oct 2026'
    if x0.count(old_ceiling) != 1:
        refuse('%s does not pin the walker ceiling where this round '
               'expects - PQ-1 must be applied' % X0)
    nx0 = x0.replace(
        old_ceiling,
        'WALKERS_OWN_ROOT_MAX = 49   # LB-1, 10 Oct 2026 - PQ-1 left it\n'
        '# at 50 and said it may only FALL. test_label_bold is the census\n'
        '# this round converts, so it falls by one and the gain is locked\n'
        '# in.  (was 50)   # PQ-1, 10 Oct 2026', 1)

    wd = read(WD)
    for was, now, why in (
            ('CONVERTED_N = 49   # PQ-1, 10 Oct 2026',
             'CONVERTED_N = 51   # LB-1, 10 Oct 2026 - 49 + test_label_bold'
             ', freed here, plus this round own suite'
             '   # PQ-1, 10 Oct 2026',
             'CONVERTED'),
            ('WAITING_N = 13   # PQ-1, 10 Oct 2026',
             'WAITING_N = 12   # LB-1, 10 Oct 2026 - test_label_bold came '
             'off   # PQ-1, 10 Oct 2026', 'WAITING'),
            ('CEILING = 50   # PQ-1, 10 Oct 2026',
             'CEILING = 49   # LB-1, 10 Oct 2026 - one census converted'
             '   # PQ-1, 10 Oct 2026', 'the ceiling')):
        if wd.count(was) != 1:
            refuse('%s does not pin %s where this round expects - PQ-1 must '
                   'be applied' % (WD, why))
        wd = wd.replace(was, now, 1)
    nwd = wd

    pq = read(PQ)
    old_pin = """for name, val in (('CONVERTED_N', 49), ('WAITING_N', 13),
                  ('CEILING', 50)):
    ok(re.search(r'%s = %d\\b' % (name, val), wd) is not None,
       '  test_waiting_down %s is %d' % (name, val),
       re.search(r'%s = \\d+' % name, wd).group(0) if
       re.search(r'%s = \\d+' % name, wd) else '?')
tr = read(os.path.join(ROOT, 'test_tree_roots.py'))
ok('WALKERS_OWN_ROOT_MAX = 50' in tr,
   '  and the walkers ceiling is 50 - that file says it may only FALL and '
   'invites the round that converts a census to lower it')
"""
    if pq.count(old_pin) != 1:
        refuse('%s does not pin the counters where this round expects' % PQ)
    new_pin = '''# LB-1, 10 Oct 2026 - THESE WERE PINNED AS LITERALS AND THE CLAIM WAS
# NEVER THE LITERAL. 49, 13 and 50 were true the day PQ-1 shipped and
# false the moment any later round converted a census - which LB-1 did,
# one round later, and this section failed on a system that was working
# exactly as intended.
#
# What PQ-1 meant is that test_waiting_down's constants are NOT STALE.
# Read against the live register that is what it says, and no round
# after this one has to come back and edit the number.
tr = read(os.path.join(ROOT, 'test_tree_roots.py'))


def _pinned(text, name):
    m = re.search(r'%s = (\\d+)' % name, text)
    return int(m.group(1)) if m else None


for name, live, what in (('CONVERTED_N', len(T.CONVERTED), 'CONVERTED'),
                         ('WAITING_N', len(T.WAITING), 'WAITING')):
    ok(_pinned(wd, name) == live,
       '  test_waiting_down %s agrees with alv_tree.%s, which holds %d'
       % (name, what, live), _pinned(wd, name))
ok(_pinned(wd, 'CEILING') == _pinned(tr, 'WALKERS_OWN_ROOT_MAX'),
   '  and its CEILING agrees with test_tree_roots WALKERS_OWN_ROOT_MAX',
   '%s vs %s' % (_pinned(wd, 'CEILING'),
                 _pinned(tr, 'WALKERS_OWN_ROOT_MAX')))
ok(_pinned(tr, 'WALKERS_OWN_ROOT_MAX') <= 50,
   '  and the walkers ceiling is at most the 50 PQ-1 left - that file '
   'says it may only FALL, and LB-1 took it to %d'
   % _pinned(tr, 'WALKERS_OWN_ROOT_MAX'))
'''
    npq = pq.replace(old_pin, new_pin, 1)


    # ---------------------------------------------------------------- 5
    tree = read(TREE)
    held_line = ("    'test_label_bold.py': 'pages  plain field labels the "
                 "sweep has not named',\n")
    if tree.count(held_line) != 1:
        refuse('%s is not on alv_tree.WAITING where this round expects it'
               % HELD)
    ntree = tree.replace(held_line, '', 1)
    conv_anchor = "    'test_required_promise.py',\n]"
    if ntree.count(conv_anchor) != 1:
        refuse('alv_tree.CONVERTED does not end where this round expects')
    ntree = ntree.replace(
        conv_anchor,
        "    'test_required_promise.py',\n"
        "    # LB-1, 10 Oct 2026 - off WAITING. It was held because the\n"
        "    # CRS forms carried plain field labels it had never seen,\n"
        "    # being on a root it did not walk. The labels are bold now\n"
        "    # and the walk is wide.\n"
        "    'test_label_bold.py',\n"
        "    # LB-1 - and this round's own suite, wide from birth.\n"
        "    'test_label_weight.py',\n]", 1)

    rounds = read(ROUNDS)
    r_anchor = "    '.bak_crsprint',\n"
    if rounds.count(r_anchor) != 1:
        refuse('alv_rounds.ROUNDS does not end with D-5\'s predecessor - '
               'PQ-1 must be applied and still be last')
    nrounds = rounds.replace(r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(PS1)
    p_anchor = "    'test_cashflow_cards.py'\n)"
    if ps.count(p_anchor) != 1:
        refuse('the $suites anchor is not in %s exactly once - D-5 must be '
               'applied and still be last' % PS1)
    nps = ps.replace(p_anchor,
                     "    'test_cashflow_cards.py',\n    '%s'\n)" % SUITE, 1)

    # ---------------------------------------------------------------- 6
    # VERIFIED, THEN WRITTEN. Nothing above has touched the tree.
    if CHECK:
        print('')
        print('LB-1  check only - nothing written')
        print('LB-1  would add base\'s absolute-700 guard')
        print('LB-1  would wrap %d CRS field label(s) on %d page(s)'
              % (n_crs, len(CRS)))
        print('LB-1  would remove %d whole .form-group label rule(s)' % n_wt)
        print('LB-1  would widen %s and take it off WAITING' % HELD)
        return 0

    for p, t in [(base_p, nb)] + list(crs_edits.items()) \
            + list(wt_edits.items()) \
            + [(os.path.join(root, HELD), nheld),
               (os.path.join(root, X0), nx0),
               (os.path.join(root, WD), nwd),
               (os.path.join(root, PQ), npq),
               (os.path.join(root, TREE), ntree),
               (os.path.join(root, ROUNDS), nrounds),
               (os.path.join(root, PS1), nps)]:
        backup(p)
        write(p, t)

    print('')
    print('LB-1  base pins <strong> inside a field label to an absolute 700')
    print('LB-1  %d CRS field label(s) wrapped on %d page(s) - %d whole, '
          '%d name-only' % (n_crs, len(CRS), n_crs - len(PART), len(PART)))
    print('LB-1  %d whole .form-group label rule(s) removed - every one of '
          'them' % n_wt)
    print('LB-1  held nothing but a weight')
    print('LB-1  %s widened to every root, Django-aware, off WAITING'
          % HELD)
    print('LB-1  and the three counters that count it: CONVERTED 49 to '
          '51, WAITING')
    print('LB-1  13 to 12, the walker ceiling 50 to 49')
    print('LB-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
