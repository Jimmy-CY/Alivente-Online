# -*- coding: utf-8 -*-
"""apply_form_card_radius.py - round FC-1, 11 Oct 2026.

ON A PHONE, ONE COMPONENT WAS WEARING FOUR CORNERS.

base owns `.form-card` completely - gradient, border, radius, padding,
margin, shadow - and at 768px it changes ONE thing, the padding. Then
twenty-one pages add a phone-only rule that beats its radius, in three
different values:

    12px   base's own, wherever no page overrides it
    10px   12 pages - the plurality, AND NOT A TOKEN
     8px    6 pages - which is exactly var(--alv-radius)
     6px    3 pages - written as var(--alv-radius-sm)

Rendered side by side at 390px those are four visibly different cards of
the same component.

THE NOTE THAT LOGGED THIS SAID "12 pages say 10px, 6 say 8px - a real
disagreement needing a decision". That read as two pages arguing. What
is actually there is twenty-one pages overriding base, which is a
different and more ordinary thing: base already said it, and nobody
removed the copies.

WHAT WAS CHOSEN, AND WHY NOT THE PLURALITY
------------------------------------------
base gains `border-radius: var(--alv-radius)` - 8px - in the phone block
it already has. Six pages already say exactly that, it is a TOKEN, and
tightening 12px to 8px on a 390px-wide card is the direction a radius
usually goes as a box gets smaller.

10px would have been the plurality and was refused: it is not one of
base's radius tokens, so adopting it means minting a third radius for a
single component. That is the case D-12 was built to close.

WHAT COMES OUT, AND THE ONE SHAPE THAT IS NOT A WHOLE RULE
-----------------------------------------------------------
    18 rules hold a radius AND NOTHING ELSE - the whole rule goes
     3 rules also set `margin-bottom: 14px` - ONLY the radius goes

Taking the whole rule on those three would silently take a margin with
it. A round that removes more than it measured is how a tidy-up becomes
a regression.

WHAT IS NAMED AND LEFT
----------------------
THOSE THREE MARGINS. petty_cash_add, suppliers_add and suppliers_edit
set `margin-bottom: 14px` on a phone against base's 22px. That is a
second disagreement about the same component and it wants its own look -
this round was agreed as the radius, and a round that changes two things
cannot say which one moved the picture.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_fcard'
SUITE = 'test_form_card_radius.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
DW = 'test_dead_weight.py'
CHECK = False

BASE_ANCHOR = '    .form-card    { padding: 16px 14px; }\n'
BASE_NEW = ('    /* FC-1, 11 Oct 2026 - AND THE RADIUS, SAID HERE RATHER\n'
            '       than on twenty-one pages. base says 12px at every\n'
            '       width above this; measured, 21 pages overrode that on\n'
            '       a phone with 10px, 8px or 6px, so one component wore\n'
            '       four corners. 8px is var(--alv-radius) and six of the\n'
            '       twenty-one already said exactly it. The plurality was\n'
            '       10px and was refused - it is not a token, and minting\n'
            '       a third radius for one component is the case D-12\n'
            '       closed.                   [test_form_card_radius.py] */\n'
            '    .form-card    { padding: 16px 14px;\n'
            '                    border-radius: var(--alv-radius); }\n')

# 18 whole rules, by the text they are written in.
WHOLE = (
    ('.form-card { border-radius: 10px; }', (
        'finance_expense_add.html', 'finance_expense_edit.html',
        'finance_expense_line_types_add.html',
        'finance_expense_line_types_edit.html',
        'finance_expense_types_add.html', 'finance_expense_types_edit.html',
        'finance_revenue_add.html', 'finance_revenue_edit.html',
        'finance_revenue_line_types_add.html',
        'finance_revenue_line_types_edit.html',
        'finance_revenue_types_add.html', 'finance_revenue_types_edit.html')),
    ('.form-card { border-radius: 8px; }', (
        'my_profile.html', 'user_add.html', 'user_edit.html',
        'user_permissions.html', 'workspace_add.html',
        'workspace_edit.html')),
)

# 3 rules that keep their margin.
PARTIAL = ('petty_cash_add.html', 'suppliers_add.html', 'suppliers_edit.html')
PARTIAL_DECL = ' border-radius: var(--alv-radius-sm);'

N_WHOLE = 18
N_PARTIAL = 3


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
    raise SystemExit('FC-1 REFUSED: %s' % msg)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    sys.path.insert(0, root)
    import alv_tree as T
    import alv_cssrules as R

    base_p = T.path_of('base.html')

    # ---------------------------------------------------------------- 0
    if 'FC-1, 11 Oct 2026' in read(base_p):
        print('FC-1  already applied')
        return 0

    if not os.path.isfile(SUITE):
        refuse('%s is not on disk - the suite ships with the round' % SUITE)

    # ---------------------------------------------------------------- 1
    b = read(base_p)
    if b.count(BASE_ANCHOR) != 1:
        refuse('base.html does not hold its phone .form-card rule exactly '
               'once in the shape this round reads')
    nb = b.replace(BASE_ANCHOR, BASE_NEW, 1)

    # ---------------------------------------------------------------- 2
    edits = {}
    n_whole = n_part = 0

    # MATCHED BY SHAPE, NOT BY LITERAL. The twenty-one rules are written
    # six different ways - CRLF and LF, one blank line or none, one space
    # or two. A first version of this patcher listed them as exact strings
    # and refused on the very first page, because the string it carried
    # had been normalised by the survey that produced it. What the round
    # is about is the DECLARATION, so that is what it finds.
    RULE = re.compile(r'[ \t]*(?<![-\w])\.form-card\s*\{([^{}]*)\}\n?')
    DECL = re.compile(r'[ \t]*border-radius:\s*[^;]+;[ \t]*\r?\n?')

    for rel in [r for _t, ps in WHOLE for r in ps] + list(PARTIAL):
        p = T.path_of(rel)
        t = read(p)
        hits = [m for m in RULE.finditer(t) if 'border-radius' in m.group(1)]
        if len(hits) != 1:
            refuse('%s: expected exactly one .form-card rule carrying a '
                   'radius, found %d' % (rel, len(hits)))
        m = hits[0]
        rest = DECL.sub('', m.group(1)).strip()
        if not rest:
            # The rule held a radius and nothing else - the whole rule goes.
            edits[p] = t[:m.start()] + t[m.end():]
            n_whole += 1
        elif re.fullmatch(r'margin-bottom:\s*14px;?', rest):
            # ONLY THE RADIUS. Taking the whole rule here would take a
            # margin this round never measured.
            body = DECL.sub('', m.group(1))
            edits[p] = t[:m.start()] + m.group(0).replace(m.group(1), body, 1) \
                + t[m.end():]
            if 'margin-bottom: 14px' not in edits[p]:
                refuse('%s: removing the radius lost the margin too' % rel)
            n_part += 1
        else:
            refuse('%s: the rule holds something this round did not measure '
                   '(%r)' % (rel, rest[:50]))

    if n_whole != N_WHOLE or n_part != N_PARTIAL:
        refuse('took %d whole rule(s) and %d declaration(s), expected %d/%d'
               % (n_whole, n_part, N_WHOLE, N_PARTIAL))

    # NOTHING ANYWHERE STILL OVERRIDES IT - checked, not assumed.
    for p, t in edits.items():
        css = re.sub(r'/\*.*?\*/', '',
                     '\n'.join(t[a:c] for a, c in R.style_spans(t)),
                     flags=re.S)
        for m in re.finditer(r'(?<![-\w])\.form-card[^{}]*\{([^}]*)\}', css):
            if 'border-radius' in m.group(1):
                refuse('%s still sets a radius after the edit'
                       % T.rel(p))

    # ---------------------------------------------------------------- 3
    tree = read(TREE)
    conv = "    'test_lines_table.py',\n]"
    if tree.count(conv) != 1:
        refuse('alv_tree.CONVERTED does not end where this round expects - '
               'IN-2 must be applied and still be last')
    ntree = tree.replace(
        conv,
        "    'test_lines_table.py',\n"
        "    # FC-1, 11 Oct 2026 - wide from birth.\n"
        "    'test_form_card_radius.py',\n]", 1)

    # THE SAME ASYMMETRY, A SECOND TIME, IN THE SAME WEEK.
    #
    # DW-1's section 7 claims "the computed value does not move" across
    # 237 probed pairs. It reads each PAGE as DW-1 left it - correctly,
    # and it says so in a note - and then renders it against BASE AS IT
    # IS TODAY. So a later round that changes a base value makes DW-1's
    # suite report a move that DW-1 did not make. FC-1 changes exactly
    # one: customer_form's .form-card radius, 12px to 8px on a phone,
    # which is this round working.
    #
    # IN-2 fixed the identical fault in test_dr2_spelling one round ago.
    # Two instances in a week is a pattern worth the name: A SUITE THAT
    # FREEZES ONE SIDE OF A COMPARISON AND LETS THE OTHER MOVE IS NOT
    # COMPARING ANYTHING. as_left_by exists so a later round cannot break
    # an older suite, and it only works applied to both sides.
    #
    # ONLY SECTION 7's COPY MOVES. braw is read in four other places
    # where live base is what is wanted; a blanket change would be this
    # round deciding something it has not measured.
    dw = read(DW)
    old_css = '    base_css = css_of(braw)\n'
    if dw.count(old_css) != 1:
        refuse('%s does not build section 7 base CSS where this round '
               'expects' % DW)
    ndw = dw.replace(
        old_css,
        '    # FC-1, 11 Oct 2026 - AS DW-1 LEFT IT, like the pages beside\n'
        '    # it. This was live base against a frozen page, so any later\n'
        '    # round that changed a base value was reported here as a move\n'
        '    # DW-1 had made. One side frozen and the other moving is not\n'
        '    # a comparison. The other four uses of braw stay live - they\n'
        '    # ask different questions.\n'
        '    base_css = css_of(as_dw1_left(T.path_of(\'base.html\')))\n', 1)

    wd = read(WD)
    old_n = 'CONVERTED_N = 52'
    if wd.count(old_n) != 1:
        refuse('%s does not pin CONVERTED_N at 52 - IN-2 must be applied'
               % WD)
    nwd = wd.replace(
        old_n,
        'CONVERTED_N = 53   # FC-1, 11 Oct 2026 - test_form_card_radius '
        'joins   # (was 52)', 1)

    rounds = read(ROUNDS)
    r_anchor = "    '.bak_lines',\n"
    if rounds.count(r_anchor) != 1:
        refuse('alv_rounds.ROUNDS does not end with IN-2')
    nrounds = rounds.replace(r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(PS1)
    p_anchor = "    'test_lines_table.py'\n)"
    if ps.count(p_anchor) != 1:
        refuse('the $suites anchor is not in %s exactly once - IN-2 must be '
               'applied and still be last' % PS1)
    nps = ps.replace(p_anchor,
                     "    'test_lines_table.py',\n    '%s'\n)" % SUITE, 1)

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('')
        print('FC-1  check only - nothing written')
        print('FC-1  would give base one phone radius, var(--alv-radius)')
        print('FC-1  would remove %d whole rule(s) and %d declaration(s) '
              'from' % (n_whole, n_part))
        print('FC-1  rules that keep their margin')
        return 0

    for p, t in [(base_p, nb)] + list(edits.items()) \
            + [(os.path.join(root, DW), ndw),
               (os.path.join(root, WD), nwd),
               (os.path.join(root, TREE), ntree),
               (os.path.join(root, ROUNDS), nrounds),
               (os.path.join(root, PS1), nps)]:
        backup(p)
        write(p, t)

    print('')
    print('FC-1  base says the phone radius once: var(--alv-radius), 8px')
    print('FC-1  %d whole rule(s) removed, and %d radius declaration(s) out '
          'of' % (n_whole, n_part))
    print('FC-1  rules that keep the margin they also carry')
    print('FC-1  one component, one corner - it wore four')
    print('FC-1  and DW-1 section 7 now reads base the way it already')
    print('FC-1  read the pages - the second suite this week that was')
    print('FC-1  comparing a frozen side against a moving one')
    print('FC-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
