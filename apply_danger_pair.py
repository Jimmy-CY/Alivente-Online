# -*- coding: utf-8 -*-
"""apply_danger_pair.py - round DG-1, 17 Oct 2026.

ONE DELETE BUTTON NEVER JOINED THE PAIR.

E12, banked 12 Oct: "D-1's height census selects six position tones and
no danger tone, so one unpaired `btn action-danger btn-sm` on
act_expense is invisible to it."

Re-measured 17 Oct, and it is sharper than that. The house form for a
destructive button is BOTH classes - `action-secondary action-danger` -
because base draws `.action-danger` outlined at rest and filled only on
hover, which makes it a MODIFIER on a secondary button and not a tone of
its own. CC-2 ran into this yesterday from the other side: a footer
Delete written as `action-danger` alone made the button GATE call the
page drifting, and the page settled it two modals below.

Three buttons in the application carry the pair. One carries the
modifier alone:

    act_expense.html        btn action-danger btn-sm              <- this
    import_recipe.html      btn action-secondary action-danger btn-sm
    preview_imported_recipe btn action-secondary action-danger btn-sm

And its own sibling, two lines above it in the same row, is
`btn action-secondary btn-sm`. The row was written one button at a time.

WHY IT WAS INVISIBLE. The button is inside a JavaScript template
string, so the censuses that walk markup never saw it, and the height
census D-1 selects on position tones - of which this button has none.
E11 is the standing finding about script-built buttons; this is one.

AND THE SUITE THAT COUNTS LV-1's WORK READS THE TREE LIVE

    test_leave_decided asserts that 25 buttons changed class, comparing
    the live file against LV-1's backup. Adding `action-secondary` to a
    26th button on one of LV-1's seventeen templates makes that 26 -
    not because LV-1 did more, but because the suite is asking today's
    tree a question about 16 October.

    That is the fault AS-1's census measured across 249 suites and the
    one DT-1 and WM-1 have already been re-pointed for. `as_left_by` is
    imported in that file and used further down it; this is the one
    place it was not.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_dangerpair'
PAGE = 'act_expense.html'
SUITE = 'test_leave_decided.py'
ME = 'test_danger_pair.py'
PATCHER = 'apply_danger_pair.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 99, 100
ALIAS_WAS, ALIAS_NOW = 107, 109
ALIAS_P_WAS, ALIAS_S_WAS = 54, 53
ALIAS_P_NOW, ALIAS_S_NOW = 55, 54

BTN_WAS = '''                <button type="button" class="btn action-danger btn-sm" onclick="deleteInvoiceDocument(${expenseId})">'''
BTN_NOW = '''                {# DG-1, 17 Oct 2026 - the pair, not the modifier alone. #}
                {# base draws .action-danger outlined at rest and filled #}
                {# only on hover, so it modifies a secondary button #}
                {# rather than being a tone of its own. The Replace #}
                {# button two lines up is already action-secondary, and #}
                {# both recipe pages carry the pair. This row was #}
                {# written one button at a time. #}
                <button type="button" class="btn action-secondary action-danger btn-sm" onclick="deleteInvoiceDocument(${expenseId})">'''

LV_WAS = """    a, b = code_only(read(p)), code_only(read(p + SUFFIX))"""
LV_NOW = """    # DG-1, 17 Oct 2026 - AS LV-1 LEFT IT, NOT LIVE.
    #
    # This compared the LIVE file against LV-1's backup and counted the
    # class attributes that differ, which is a question about 16
    # October asked of today's tree. Any later round that touches a
    # button on one of these seventeen templates is counted as LV-1's
    # work: DG-1 added action-secondary to one and the figure went 25
    # -> 26.
    #
    # as_left_by walks ROUNDS forward and hands back the next round's
    # backup - the file as THIS round left it. It is imported at the
    # top of this suite and used further down it; this was the one
    # place it was not. AS-1's census measured this fault across 249
    # suites on 16 Oct.
    a = code_only(as_left_by(p, SUFFIX, read) if as_left_by else read(p))
    b = code_only(read(p + SUFFIX))"""


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
    raise SystemExit('DG-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)
    s = read(page)

    if 'action-secondary action-danger btn-sm" onclick="deleteInvoice' in s:
        print('DG-1  already applied - the Delete button wears the pair.')
        return 0

    out = {}

    # THE PAIR IS READ OFF THE PAGES THAT HAVE IT, not remembered.
    pairs = []
    for rel in ('import_recipe.html', 'preview_imported_recipe.html'):
        t = code_only(read(alv_tree.path_of(rel)))
        if 'action-secondary action-danger' in t:
            pairs.append(rel)
    if len(pairs) < 2:
        refuse('only %d page(s) carry the pair, so there is no house form '
               'to join: %s' % (len(pairs), pairs))
    base = read(alv_tree.path_of('base.html'))
    if '.action-danger' not in base:
        refuse('base.html no longer declares .action-danger')

    s = swap(s, BTN_WAS, BTN_NOW, '%s (the Delete button)' % PAGE)
    b = code_only(s)
    if re.search(r'class="btn action-danger\b', b):
        refuse('%s still has a Delete that wears the modifier alone' % PAGE)
    # TWO, NOT ONE. The page already had a correct pair -
    # #confirmDeleteBtn in the delete-confirmation footer - which is
    # itself the evidence that the row this round fixes was written
    # one button at a time rather than to a rule nobody knew.
    had = code_only(read(page)).count('action-secondary action-danger')
    if had != 1:
        refuse('%s carried %d paired button(s) before this round, '
               'expected the one in the delete confirmation' % (PAGE, had))
    if b.count('action-secondary action-danger') != 2:
        refuse('%s: %d paired button(s) after, expected 2'
               % (PAGE, b.count('action-secondary action-danger')))
    bad = [i + 1 for i, ln in enumerate(s.split('\n'))
           if ln.count('{#') != ln.count('#}')]
    if bad:
        refuse('%s: a Django comment outlives its line, at %s' % (PAGE, bad))
    out[page] = s

    # ------------------------------------------------ the suite it moves
    sp = os.path.join(root, SUITE)
    q = read(sp)
    if 'as_left_by' not in q:
        refuse('%s does not import as_left_by, so re-pointing it would '
               'break it instead of fixing it' % SUITE)
    q = swap(q, LV_WAS, LV_NOW, '%s (the live read)' % SUITE)
    try:
        import ast
        ast.parse(q)
    except SyntaxError as e:
        refuse('%s would no longer parse - %s' % (SUITE, e))
    if 'a, b = code_only(read(p)), code_only(read(p + SUFFIX))' in q:
        refuse('%s still reads the tree live' % SUITE)
    out[sp] = q

    # -------------------------------------------------------- registered
    p = os.path.join(root, PS1)
    t = read(p)
    t = swap(t, """    'test_invoice_icon.py'
)""", """    'test_invoice_icon.py',
    'test_danger_pair.py'
)""", '%s ($suites)' % PS1)
    t = swap(t, """    # -------------------------------------------- HL-1, 12 Oct 2026""",
             """    # ------------------------------------------------- DG-1, 17 Oct 2026
    @{ File = 'pages\\templates\\act_expense.html'; Text = 'action-secondary action-danger btn-sm'; What = 'DG-1: the Delete button wears the house pair' },
    # -------------------------------------------- HL-1, 12 Oct 2026""",
             '%s ($sentinels)' % PS1)
    out[p] = t

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), """    'test_invoice_icon.py',
]""", """    'test_invoice_icon.py',
    # DG-1, 17 Oct 2026 - one script-built Delete button joins the
    # action-secondary action-danger pair, and the suite that counts
    # LV-1's work stops counting later rounds as LV-1's. Wide from
    # birth.
    'test_danger_pair.py',
]""", '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), """    '.bak_invoiceicon',""",
                  """    '.bak_invoiceicon',
    # DG-1, 17 Oct 2026 - E12, re-measured and sharper than banked.
    '.bak_dangerpair',""", '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'DG-1, 17 Oct 2026 - this round own suite',
                  '%s (CONVERTED_N)' % WD)

    import glob as _glob
    _al = [os.path.basename(f)
           for f in sorted(_glob.glob(os.path.join(root, '*.py')))
           if re.search(r'^code_only\s*=\s*alv_tree\.code_only',
                        read(f), re.M)]
    _pat = [f for f in _al if f.startswith('apply_')]
    _sui = [f for f in _al if f.startswith('test_')]
    if len(_al) < ALIAS_NOW or len(_pat) < ALIAS_P_NOW \
            or len(_sui) < ALIAS_S_NOW:
        refuse('the alias count on disk is %d (%d patchers, %d suites) and '
               'this round would write %d (%d, %d) - more than exist'
               % (len(_al), len(_pat), len(_sui),
                  ALIAS_NOW, ALIAS_P_NOW, ALIAS_S_NOW))

    p = os.path.join(root, CO)
    t2 = bump(read(p), 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
              'DG-1, 17 Oct 2026 - this round own patcher and suite',
              '%s (the alias count)' % CO)
    t2 = swap(t2, "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_WAS, ALIAS_S_WAS),
              "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_NOW, ALIAS_S_NOW),
              '%s (the alias split)' % CO)
    out[p] = t2

    if CHECK:
        print('DG-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('DG-1 applied.')
    print('   the Delete button wears action-secondary action-danger')
    print('   and test_leave_decided counts LV-1 work as LV-1 left it')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
