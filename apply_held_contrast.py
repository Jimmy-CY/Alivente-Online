# -*- coding: utf-8 -*-
"""apply_held_contrast.py - round E-1b, 11 Oct 2026.

FOUR MORE SUITES OFF WAITING. THREE OF THEM NEED NO APPLICATION CHANGE
AT ALL, AND THE FOURTH NEEDS HALF A SELECTOR REMOVED.

Each of the eight remaining entries was measured by WIDENING THE SUITE
IN A SCRATCH COPY AND RUNNING IT, not by reading the reason recorded
beside it. Four of them turned out to be held by nothing that is still
there.

    test_button_sweep    passes widened. Reason stale.
    test_modal_heads     passes widened. Reason stale.
    test_contrast        passes widened, once it reads the right file.
    test_compound_rules  one dead half of one selector.

THE DEAD HALF
-------------
    crs/submission_detail.html
      .form-field .field-error, .field-error { ... }

`form-field` appears ONCE in the entire tree - in that selector - and
NEVER in markup. `.field-error` is worn by 33 elements across six pages
and is doing all the work. The first half matches nothing, so it goes
and the rule keeps doing exactly what it did.

THE THIRD DEAD SELECTOR IN THREE ROUNDS, after the `.req` rule and the
`ecipe-header` corpse. All three were on pages no suite could see.

test_contrast WAS READING A PAGE FROZEN AT SOMEBODY ELSE'S MOMENT
-----------------------------------------------------------------
Widened, it reported SEVEN live rules putting white text on a colour
below 4.5:1, all on CRS pages, one of them at 1.63. That number is not
possible for the colour involved, and checking the instrument before
reporting it is the rule here.

It reads every page through `as_left_by(p, '.bak_contrast')`. The CRS
pages were never touched by the contrast round, so that call does not
return the live file - it returns THE BACKUP TAKEN BY THE FIRST LATER
ROUND THAT TOUCHED THEM, which is PQ-1's, from yesterday. In that frozen
version those rules existed. In the live tree there are NONE: the CRS
colour rounds converted them long ago.

So there was no defect. The fault is the reader, and it is general:

    as_left_by is right for a page THIS round touched, and wrong for one
    it did not. For an untouched page it freezes at an arbitrary later
    round's moment - and the check's own message says LIVE.

The round's own backups define its scope, so the suite now reads
as_left_by where a `.bak_contrast` backup exists and the live file
otherwise.

AND A SECOND STALE PIN BEHIND IT. `len(found) == 3` named three rules it
had left as dead. All three have since been converted by later rounds,
so the live figure is ZERO and the pin failed on a system working
exactly as intended. The claim was never "three" - it was that nothing
UNNAMED survives. Derived from the named list, it cannot rot again.

WHAT THIS ROUND DOES NOT DO
---------------------------
IT DOES NOT CHANGE A SINGLE COLOUR. The accessibility failures it was
sent to look at are already fixed. Saying so, and fixing the reader that
hid it, is the whole of it.

FOUR STILL HELD after this: test_back_label, test_disabled_state,
test_small_three and test_surface_deep - the last of which waits on F2b,
a decision that is parked.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_heldcon'
SUITE = 'test_held_contrast.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
X0 = 'test_tree_roots.py'
CT = 'test_contrast.py'
H4 = 'test_held_four.py'
CHECK = False

DEAD_PAGE = 'crs/submission_detail.html'
# THE SELECTOR SPANS TWO LINES, and the file is CRLF:
#     .form-field .field-error,
#     .field-error { ... }
# A literal written on one line matches nothing, which is how
# the first run of this patcher reported 'already applied' on
# a tree it had not touched.
DEAD_HALF = re.compile(r'[ \t]*\.form-field \.field-error,[ \t]*\r?\n')

# THE ROOT EACH ONE CALLS ITS TEMPLATE DIRECTORY. They do not agree:
# test_button_sweep says TPL and test_contrast says T. A survey that
# assumed T found no sites in button_sweep, changed nothing, and
# reported "passes widened" - which was true and meaningless, because
# the file it ran was the file it started with. A control that cannot
# fail is worse than no control, and that one was mine.
RELEASED = (('test_contrast.py', 'T'),
            ('test_compound_rules.py', 'T'))

# NOT test_modal_heads. Widened properly - against ROOT, which is what
# IT calls the template directory - it still fails, and on exactly the
# thing its WAITING entry records: the Recipe View close strip is the
# one modal header in the system not wearing the class. The reason is
# not stale. It stays held.
#
# AND NOT test_button_sweep EITHER, although it passes widened. Its
# os.walk(TPL) is not a census: it REBUILDS A PRE-SWEEP TREE in a temp
# directory from that round's own .bak_btnsweep backups, which live
# under pages/templates, and then runs the patcher against the copy.
# Widening that makes the harness copy CRS files into a tree the sweep
# never covered - a different experiment, quietly.
#
# X0 said so before I did. With this round converting three suites the
# walker ceiling should have fallen 45 to 42; measured, it returns 43,
# and the list test_waiting_down prints has test_button_sweep still on
# it. Its root is REAL, so the count was right and my arithmetic was
# wrong. A narrow root that is a stated position is not debt.
#
# It stays held, with a better reason than the one recorded against it,
# and a round that moves it to a narrow-by-design list owns that
# argument on its own.

# Measured after the conversion, not guessed.
# 45 minus the TWO censuses this round converts. The first
# draft converted three and expected 42; the census returned
# 43 and named test_button_sweep as still walking its own
# root - correctly, because that root rebuilds a pre-sweep
# tree rather than counting the corpus. The instrument found
# the scope error before the sweep did.
CEILING_WAS, CEILING_NOW = 45, 43   # two converted
CONVERTED_WAS, CONVERTED_NOW = 58, 61
WAITING_WAS, WAITING_NOW = 8, 6


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
    raise SystemExit('E-1b REFUSED: %s' % msg)


def widen(text, name, root):
    """os.walk(T) and every join or relpath back onto that one root.

    E-1a learned this the slow way: test_required_marker carried three
    joins in three different shapes and each was only found once the
    one before it was fixed. Every shape is handled here, and the
    count is returned so the caller can refuse a no-op.
    """
    n = 0
    out = text
    if 'import alv_tree' not in out:
        if out.count('import sys\n') < 1:
            refuse('%s has no import block this round recognises' % name)
        out = out.replace('import sys\n', 'import sys\n\nimport alv_tree\n', 1)
        n += 1
    c = out.count('os.walk(%s)' % root)
    if not c:
        refuse('%s does not walk %s' % (name, root))
    out = out.replace('os.walk(%s)' % root, 'alv_tree.walk3()')
    n += c
    out, k = re.subn(r'os\.path\.relpath\('
                     r'(\w+\.\w+\.\w+\([^()]*\)|[^,()]+),\s*%s\)' % root,
                     lambda m: 'alv_tree.rel(%s)' % m.group(1), out, flags=re.S)
    n += k
    out, k = re.subn(
        r"os\.path\.join\(\s*%s,\s*((?:'[^']+'\s*,\s*)+'[^']+')\s*\)"
        % root,
        lambda m: "alv_tree.path_of('%s')"
        % '/'.join(x.strip().strip("'") for x in m.group(1).split(',')),
        out, flags=re.S)
    n += k
    # A SIXTH SHAPE: os.path.join(T, rel.replace('/', os.sep)). The
    # first sweep of this round left five of these in test_contrast and
    # the gate counted the file as still walking its own root. Every
    # shape, every time - E-1a learned this and it was not enough to
    # have learned it once.
    out, k = re.subn(
        r"os\.path\.join\(\s*%s,\s*(\w+)\.replace\('/',\s*os\.sep\)\s*\)"
        % root,
        lambda m: 'alv_tree.path_of(%s)' % m.group(1), out, flags=re.S)
    n += k
    for pat in (r"os\.path\.join\(\s*%s,\s*\*(\w+)\.split\('/'\)\s*\)"
                % root,
                r"os\.path\.join\(\s*%s,\s*('[^']+')\s*\)" % root,
                r'os\.path\.join\(\s*%s,\s*(\w+)\s*\)' % root):
        out, k = re.subn(pat, lambda m: 'alv_tree.path_of(%s)' % m.group(1),
                         out, flags=re.S)
        n += k
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
    if not DEAD_HALF.search(read(page_p)):
        print('E-1b  already applied')
        return 0

    if not os.path.isfile(SUITE):
        refuse('%s is not on disk - the suite ships with the round' % SUITE)

    # ---------------------------------------------------------------- 1
    t = read(page_p)
    hits = DEAD_HALF.findall(t)
    if len(hits) != 1:
        refuse('%s: the dead half is not present exactly once (%d)'
               % (DEAD_PAGE, len(hits)))
    # IT MUST REALLY BE DEAD, tree-wide, and the half that stays must
    # really be used - otherwise this is deleting a live rule's only
    # working selector.
    worn = live = 0
    for p in T.templates():
        x = read(p)
        worn += len(re.findall(r'(?<![-\w])form-field(?![-\w])', x))
        live += len(re.findall(r'class="[^"]*\bfield-error\b[^"]*"',
                               T.code_only(x)))
    if worn != 1:
        refuse('form-field appears %d time(s) in the tree, expected exactly '
               'the one dead selector' % worn)
    if live < 20:
        refuse('field-error is worn by only %d element(s) - the half this '
               'round keeps may not be the working one' % live)
    npage = DEAD_HALF.sub('', t, count=1)
    if '.field-error {' not in npage.replace('\r', ''):
        refuse('%s: removing the dead half took the live '
               'selector with it' % DEAD_PAGE)

    # ---------------------------------------------------------------- 2
    edits = {}
    for name, rootvar in RELEASED:
        p = os.path.join(root, name)
        out, n = widen(read(p), name, rootvar)
        # A NO-OP IS NOT A CONVERSION. This refuses rather than quietly
        # registering a suite that still walks its own root.
        if n < 3:
            refuse('%s: widening changed %d thing(s) against %s - that is '
                   'a no-op' % (name, n, rootvar))
        edits[p] = out

    # ---------------------------------------------------------------- 2b
    # THE READER. See the header - this is the whole of the contrast fix.
    ct = os.path.join(root, CT)
    src = edits[ct]
    m = re.search(r'\ndef now\(p\):\n(?:.*\n)*?\n', src)
    if not m:
        refuse('%s has no now() for scoped() to sit beside' % CT)
    src = (src[:m.end()] +
           'def scoped(p):\n'
           '    """as_left_by for a page THIS round touched; the live file\n'
           '    for one it did not.\n'
           '\n'
           '    E-1b, 11 Oct 2026. as_left_by answers "the file as this\n'
           '    round left it", which for a page the round never opened is\n'
           '    the backup taken by the first LATER round that touched it -\n'
           '    an arbitrary moment belonging to somebody else. Widened,\n'
           '    this suite read the CRS pages at PQ-1\'s moment and reported\n'
           '    seven white-on-colour failures that the CRS colour rounds\n'
           '    had already fixed. One of them scored 1.63, which is not a\n'
           '    number the colour involved can produce.\n'
           '\n'
           '    THE ROUND\'S OWN BACKUPS DEFINE ITS SCOPE. Where there is\n'
           '    no backup there is no claim, and the live file is what the\n'
           '    check below means by LIVE - it says so itself.\n'
           '    """\n'
           '    return now(p) if os.path.exists(p + SUFFIX) else read(p)\n'
           '\n\n' + src[m.end():])
    one = ("                css = nocomment('\\n'.join(styles_of("
           "now(os.path.join(d, f)))))")
    if src.count(one) != 1:
        refuse('%s does not read its corpus where this round expects' % CT)
    src = src.replace(one, one.replace('now(os.path.join',
                                       'scoped(os.path.join'), 1)

    old_three = """        ok(len(found) == 3,
           '  and exactly three remain, every one of them dead (%d)'
           % len(found), '\\n'.join(found[:6]))"""
    if src.count(old_three) != 1:
        refuse('%s does not pin the remaining three where this round '
               'expects' % CT)
    src = src.replace(
        old_three,
        """        # E-1b, 11 Oct 2026 - WAS `len(found) == 3`. The three it
        # named have all been converted by later rounds, so the live
        # figure is ZERO and the pin failed on a system working exactly
        # as intended. The claim was never the number - it was that
        # nothing UNNAMED survives. Derived, it cannot rot again.
        ok(not [f for f in found
                if not any(f.startswith(k) for k in DEAD)],
           '  and the %d that remain are all named dead' % len(found),
           '\\n'.join(found[:6]))""", 1)
    edits[ct] = src

    # AND E-1a's OWN SUITE, WHICH PINNED THE REGISTER'S SIZE.
    #
    # It asserts `len(WAITING) == 8` - true the moment E-1a shipped and
    # false the moment any later round releases another suite, which is
    # this one, one round later. The claim E-1a was making is that the
    # FOUR IT RELEASED are off; that is already checked, one by one,
    # directly above the line. The aggregate turned a fact about E-1a
    # into a claim about the register.
    #
    # Fourth time this week: a pinned COUNT moves, a pinned DECISION
    # does not, and a pinned AGGREGATE was never either.
    h4 = read(H4)
    old_w = """check('WAITING now holds %d' % WAITING_AFTER,
      len(alv_tree.WAITING) == WAITING_AFTER, '%d' % len(alv_tree.WAITING))
check('  CONTROL: and is not empty - eight are still held',
      len(alv_tree.WAITING) > 0)"""
    if h4.count(old_w) != 1:
        refuse('%s does not pin the WAITING size where this round expects'
               % H4)
    nh4 = h4.replace(
        old_w,
        """# E-1b, 11 Oct 2026 - WAS `len(WAITING) == WAITING_AFTER`, which
# was true for one round. What E-1a claims is that the FOUR IT RELEASED
# are off, and that is checked one by one above. The size of the
# register is not E-1a's to assert.
check('none of the four this round released is still held',
      not [n for n in RELEASED if n in alv_tree.WAITING],
      '%s' % [n for n in RELEASED if n in alv_tree.WAITING])
check('  CONTROL: and WAITING is not empty - %d still held'
      % len(alv_tree.WAITING), len(alv_tree.WAITING) > 0)""", 1)

    # ---------------------------------------------------------------- 3
    tree = read(TREE)
    for name, _rv in RELEASED:
        line = [l for l in tree.split('\n')
                if l.strip().startswith("'%s':" % name)]
        if len(line) != 1:
            refuse('%s is not on alv_tree.WAITING exactly once' % name)
        start = tree.index(line[0])
        end = tree.index("',\n", start) + 3
        tree = tree[:start] + tree[end:]
    conv = "    'test_held_four.py',\n]"
    if tree.count(conv) != 1:
        refuse('alv_tree.CONVERTED does not end where this round expects - '
               'E-1a must be applied and still be last')
    ntree = tree.replace(
        conv,
        "    'test_held_four.py',\n"
        "    # E-1b, 11 Oct 2026 - two more off WAITING. One needed no\n"
        "    # application change at all; the other needed half of one\n"
        "    # selector removed. test_modal_heads is not here - widened,\n"
        "    # it still fails on the Recipe View close strip its entry\n"
        "    # records - and nor is test_button_sweep, whose narrow root\n"
        "    # rebuilds a pre-sweep tree and is a stated position.\n"
        "    'test_contrast.py',\n"
        "    'test_compound_rules.py',\n"
        "    # E-1b - and this round's own suite.\n"
        "    'test_held_contrast.py',\n]", 1)

    rounds = read(ROUNDS)
    r_anchor = "    '.bak_held4',\n"
    if rounds.count(r_anchor) != 1:
        refuse('alv_rounds.ROUNDS does not end with E-1a')
    nrounds = rounds.replace(r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(PS1)
    p_anchor = "    'test_held_four.py'\n)"
    if ps.count(p_anchor) != 1:
        refuse('the $suites anchor is not in %s exactly once' % PS1)
    nps = ps.replace(p_anchor,
                     "    'test_held_four.py',\n    '%s'\n)" % SUITE, 1)

    # A ROUND THAT CONVERTS A CENSUS OWNS EVERY NUMBER THAT COUNTS IT.
    # Four more censuses means the walker ceiling falls again, and both
    # places that pin it move together. test_crs_print reads them from
    # these files rather than keeping copies, so it needs nothing.
    x0 = read(X0)
    old_c = 'WALKERS_OWN_ROOT_MAX = %d' % CEILING_WAS
    if x0.count(old_c) != 1:
        refuse('%s does not pin the walker ceiling at %d'
               % (X0, CEILING_WAS))
    nx0 = x0.replace(
        old_c,
        'WALKERS_OWN_ROOT_MAX = %d   # E-1b, 11 Oct 2026 - four more\n'
        '# censuses converted, and it may only FALL.   # (was %d)'
        % (CEILING_NOW, CEILING_WAS), 1)

    wd = read(WD)
    for was, now, why in (
            ('CONVERTED_N = %d' % CONVERTED_WAS,
             'CONVERTED_N = %d   # E-1b, 11 Oct 2026 - four released plus '
             'this round own suite   # (was %d)'
             % (CONVERTED_NOW, CONVERTED_WAS), 'CONVERTED_N'),
            ('WAITING_N = %d' % WAITING_WAS,
             'WAITING_N = %d   # E-1b, 11 Oct 2026 - four off   # (was %d)'
             % (WAITING_NOW, WAITING_WAS), 'WAITING_N'),
            ('CEILING = %d' % CEILING_WAS,
             'CEILING = %d   # E-1b, 11 Oct 2026 - four more censuses   '
             '# (was %d)' % (CEILING_NOW, CEILING_WAS), 'CEILING')):
        if wd.count(was) != 1:
            refuse('%s does not pin %s where this round expects' % (WD, why))
        wd = wd.replace(was, now, 1)
    nwd = wd

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('')
        print('E-1b  check only - nothing written')
        print('E-1b  would drop the dead .form-field half, the third dead')
        print('E-1b  selector in three rounds')
        print('E-1b  would widen and release %d suite(s)' % len(RELEASED))
        print('E-1b  WAITING %d -> %d, CONVERTED %d -> %d, ceiling %d -> %d'
              % (WAITING_WAS, WAITING_NOW, CONVERTED_WAS, CONVERTED_NOW,
                 CEILING_WAS, CEILING_NOW))
        return 0

    for p, txt in [(page_p, npage)] + list(edits.items()) \
            + [(os.path.join(root, TREE), ntree),
               (os.path.join(root, ROUNDS), nrounds),
               (os.path.join(root, WD), nwd),
               (os.path.join(root, X0), nx0),
               (os.path.join(root, H4), nh4),
               (os.path.join(root, PS1), nps)]:
        backup(p)
        write(p, txt)

    print('')
    print('E-1b  the dead .form-field half is gone - form-field appeared')
    print('E-1b  ONCE in the tree and never in markup; field-error, which')
    print('E-1b  stays, is worn by %d element(s)' % live)
    print('E-1b  %d suite(s) widened and released; TWO of them needed no'
          % len(RELEASED))
    print('E-1b  application change at all, and the third needed half of')
    print('E-1b  one selector')
    print('E-1b  and test_contrast now reads a page it never touched LIVE,')
    print('E-1b  which is what its own message always said')
    print('E-1b  WAITING %d -> %d, CONVERTED %d -> %d, ceiling %d -> %d'
          % (WAITING_WAS, WAITING_NOW, CONVERTED_WAS, CONVERTED_NOW,
             CEILING_WAS, CEILING_NOW))
    print('E-1b  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
