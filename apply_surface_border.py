# -*- coding: utf-8 -*-
"""apply_surface_border.py - round F2b, 13 Oct 2026.

A BORDER IS NAMED BY THE BORDER TOKEN.

F2a split every use of `--alv-surface-deep` into buckets and fixed the
backgrounds. It left the borders, said so, and said why: the change is
below what an eye can read, so it is a decision about naming rather than
about looking, and a round that cannot show you a difference has to ask
instead. `test_surface_deep` has been held on WAITING ever since, with
"its border uses wait on F2b" written against it.

DEMETRI DECIDED IT ON 13 OCT: convert them.

WHAT IT LOOKS LIKE - WHICH IS TO SAY, NOTHING
----------------------------------------------
    --alv-surface-deep   #e9ecef     the far stop of the panel wash
    --alv-line           #e3e8ea     the border token

    15 RGB units apart in total, 6 on the widest channel
    against paper      1.186:1  ->  1.236:1
    against surface    1.125:1  ->  1.172:1

Both are invisible either way. What changes is that a border is named by
the token that means border, so retuning one line of base retunes the
right set of things.

MEASURED TODAY, NOT COPIED FORWARD
-----------------------------------
The master list says 93 border uses across 43 pages, and that number
comes from `LEFT_BORDERS` in test_surface_deep - which reads every page
AS F2a LEFT IT. Live, today:

    81 border uses across 44 pages
    96 NON-border uses, which stay - this round is about borders

Twelve have gone since F2a, taken by later rounds that happened to
rewrite the rule holding them. The pin is not wrong; it is answering a
different question, and it keeps answering it after today because
as_left_by hands it the backups this round takes.

THREE OF THE 81 ARE NOT CONVERTED, AND THEY ARE ALL OF base
-----------------------------------------------------------
    .btn.action-secondary[disabled]
    .btn.action-primary[aria-disabled="true"]
    .btn.action-danger[aria-disabled="true"]

each writing

    background:    var(--alv-disabled-bg, var(--alv-surface-deep));
    border-color:  var(--alv-disabled-bg, var(--alv-surface-deep));

That is E-10's switched-off recipe, and the two declarations are the
SAME EXPRESSION on purpose: a disabled control is one flat block, fill
and edge together. Converting the border half would give a switched-off
button an edge a different colour from its fill - visible, and a
different decision from this one.

So base.html is not touched at all, and the one shape this round refuses
is the one where the border is MEANT to be the fill. 78 conversions, 43
pages, and the house file untouched.

IT DOES NOT RELEASE THE SUITE, AND THAT IS A MEASUREMENT
---------------------------------------------------------
I expected it to. test_surface_deep passes 259/0 and is held only from
WIDENING, and I measured the CRS root as carrying zero of these borders
- so widening looked free. It is not, and the round found out by trying.

  WIDENED AS IT STANDS the walk reaches the CRS root and `now()` -
  as_left_by(p, '.bak_surfdeep') - hands back whichever LATER round
  opened each CRS file. F2a never touched the CRS root, so that is not
  "as F2a left it". 6 BACKGROUNDS and 15 BORDERS appeared out of frozen
  backups, none of them live: #e9ecef literals the CRS rounds removed
  weeks ago. My measurement had counted the LIVE CRS files; the suite
  does not read those.

  SCOPED WITH BL-2's READER - a page with no backup of this round's
  suffix was never this round's business, so read it live - the phantoms
  go. But LEFT_BORDERS then falls 93 -> 56 and LEFT_CUSTOM 3 -> 1,
  because pages F2a never touched are read live and F2b has just
  converted them. Both pins need re-deriving, and two --future-light
  declarations on admin_apms and personal become a question this round
  has no business answering.

FOURTH OCCURRENCE of the as_left_by lesson: right for a page the round
TOUCHED, wrong for one it did not. E-1b, BL-2, test_contrast, and here.

So F2b converts the borders and stops. The held reason is REWRITTEN
rather than removed - it named a decision that has since been taken, and
it now names what actually holds the suite, with the numbers above as
the survey for whoever does it. WAITING stays at 2.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import alv_tree                                            # noqa: E402

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_surfborder'
SUITE = 'test_surface_border.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
X0 = 'test_tree_roots.py'
SD = 'test_surface_deep.py'
CO = 'test_code_only.py'
CHECK = False

OLD, NEW = 'var(--alv-surface-deep)', 'var(--alv-line)'
# A border declaration holding the token - and NOT the var() fallback,
# which is a different shape and a different decision.
BORDER = re.compile(r'border[\w-]*\s*:\s*[^;}]*' + re.escape(OLD) + r'[^;}]*;')
FALLBACK = 'var(--alv-disabled-bg, ' + OLD + ')'

N_CONVERT = 78
N_FALLBACK = 3
N_PAGES = 43
N_OTHER = 96          # non-border uses, which stay

CEILING_WAS, CEILING_NOW = 38, 38
CONVERTED_WAS, CONVERTED_NOW = 70, 71
WAITING_WAS, WAITING_NOW = 2, 2
ALIAS_WAS, ALIAS_NOW = 51, 53


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
    raise SystemExit('F2b REFUSED: %s' % msg)


def once(text, lit, where):
    n = text.count(lit)
    if n != 1:
        refuse('%s: %r appears %d time(s), expected exactly 1'
               % (where, lit[:70], n))


def convert(text):
    """Every border declaration holding the token, and nothing else.

    THE FALLBACK IS SKIPPED BY SHAPE, NOT BY PAGE. Matching on
    `var(--alv-disabled-bg, ...)` inside the declaration is what tells
    E-10's switched-off recipe from an ordinary border, and it would
    keep telling them apart if that recipe ever moved to another file.
    An exclusion list of page names would not.
    """
    n = [0]

    def sub(m):
        d = m.group(0)
        if FALLBACK in d:
            return d
        n[0] += d.count(OLD)
        return d.replace(OLD, NEW)

    return BORDER.sub(sub, text), n[0]


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED IS ASKED OF THE TREE, not of a count. The round
    # converts 78 declarations; if none is left to convert, it is done.
    if not any(convert(read(p))[1] for p in alv_tree.templates()):
        print('F2b  already applied - no plain border draws on the '
              'panel-wash token.')
        return 0

    out = {}
    pages, total = {}, 0
    for p in alv_tree.templates():
        rel = alv_tree.rel(p)
        s = read(p)
        new, n = convert(s)
        if not n:
            continue
        pages[rel] = n
        total += n
        out[p] = new

    if total != N_CONVERT:
        refuse('converted %d border use(s), the survey measured %d'
               % (total, N_CONVERT))
    if len(pages) != N_PAGES:
        refuse('touched %d page(s), the survey measured %d'
               % (len(pages), N_PAGES))

    # base IS NOT TOUCHED, and that is a result rather than a rule: its
    # only three border uses are the disabled fallback, which convert()
    # refuses by shape.
    if 'base.html' in pages:
        refuse('base.html was converted - its three border uses are E-10 '
               'switched-off recipe, where the edge is MEANT to be the fill')
    left = 0
    for p in alv_tree.templates():
        t = out.get(p, read(p))
        for m in BORDER.finditer(t):
            if FALLBACK in m.group(0):
                left += 1
            else:
                refuse('%s still has a plain border on the surface token: %s'
                       % (alv_tree.rel(p), ' '.join(m.group(0).split())[:60]))
    if left != N_FALLBACK:
        refuse('expected %d var() fallback(s) to survive, found %d'
               % (N_FALLBACK, left))

    # AND THE NON-BORDER USES ARE UNTOUCHED. A round that converted a
    # background here would be doing F2a's job again, badly.
    other = 0
    for p in alv_tree.templates():
        t = out.get(p, read(p))
        other += t.count(OLD) - sum(
            1 for m in BORDER.finditer(t) for _ in range(m.group(0).count(OLD)))
    if other != N_OTHER:
        refuse('%d non-border use(s) of the token remain, expected %d - this '
               'round is about borders' % (other, N_OTHER))

    # ---------------------------------------------------------------- 2
    # THE SUITE IS **NOT** WIDENED, AND THAT IS A MEASUREMENT.
    #
    # F2a's held reason said "its border uses wait on F2b". They do not
    # any more - but widening the suite was the other half of releasing
    # it, and widening is not clean. Tried, measured, and backed out:
    #
    #   widened as it stands, the walk reaches the CRS root and `now()`
    #   - as_left_by(p, '.bak_surfdeep') - hands back whichever LATER
    #   round opened each CRS file. F2a never touched the CRS root, so
    #   that is not "as F2a left it". It reported 6 BACKGROUNDS and 15
    #   BORDERS out of frozen backups, none of which exist live: #e9ecef
    #   literals the CRS rounds removed weeks ago.
    #
    #   scoped with BL-2's reader - a page with no backup of this
    #   round's suffix was never this round's business, so read it live
    #   - the phantom six and fifteen go. But then LEFT_BORDERS falls
    #   93 -> 56 and LEFT_CUSTOM 3 -> 1, because pages F2a never touched
    #   are now read live and F2b has just converted them. Both pins
    #   have to be re-derived, and two `--future-light` declarations on
    #   admin_apms and personal become a question this round has no
    #   business answering.
    #
    # THAT IS A SECOND ROUND INSIDE SOMEONE ELSE'S SUITE, and a round
    # that does two things cannot say which one moved. So F2b converts
    # the borders and nothing else. test_surface_deep stays on WAITING
    # with a reason that is now TRUE rather than stale: not "its borders
    # wait on a decision" - they do not - but "widened, its reader and
    # its two counts need re-deriving, and the CRS root was never F2a's
    # business". The numbers above are the survey for whoever does it.

    # ---------------------------------------------------------------- 3
    # THE HELD REASON IS REWRITTEN, NOT REMOVED. A reason recorded is
    # not a reason re-measured, and this one had gone stale in the only
    # way that matters: it named a decision that has since been taken.
    #
    # AND IT SAYS "second root", NOT "CRS". X11 asserts that no held
    # reason blames CRS, because ten CRS rounds landed and a register
    # that still points there sends the next reader to the wrong module.
    # My first wording named CRS - truthfully, as the place the phantom
    # backups come from - and X11's check fired on it. The check is
    # right and my words were the cheaper thing to change: a round that
    # rewrites someone else's control to accommodate its own prose has
    # removed a control. alv_tree's own docs call it "a SECOND template
    # root", so that is what the reason calls it.
    tree = read(os.path.join(root, TREE))
    old_reason = ("    'test_surface_deep.py':\n"
                  "        'pages  background literals survive, and its 93 "
                  "border uses wait on F2b',")
    if old_reason not in tree:
        m = re.search(r"    'test_surface_deep\.py':\n[^\n]*\n", tree)
        if not m:
            refuse('%s is not on alv_tree.WAITING in a shape this round '
                   'can rewrite' % SD)
        old_reason = m.group(0).rstrip('\n')
    once(tree, old_reason, TREE)
    tree = tree.replace(
        old_reason,
        "    'test_surface_deep.py':\n"
        "        'pages  F2b took the 78 border uses on 13 Oct, so the "
        "DECISION is '\n"
        "        'no longer what holds it. WIDENING is: as_left_by hands it "
        "second-root '\n"
        "        'backups F2a never had a claim on - 6 phantom backgrounds "
        "and '\n"
        "        '15 phantom borders - and BL-2 scoped reader fixes those "
        "but '\n"
        "        'moves LEFT_BORDERS 93 to 56 and LEFT_CUSTOM 3 to 1. Both "
        "pins '\n"
        "        'need re-deriving. [reason replaced F2b, 13 Oct 2026]',", 1)
    c_anchor = "    'test_py_code.py',\n]"
    once(tree, c_anchor, TREE)
    out[os.path.join(root, TREE)] = tree.replace(
        c_anchor,
        "    'test_py_code.py',\n"
        "    # F2b's own suite.\n"
        "    '%s',\n]" % SUITE, 1)

    rounds = read(os.path.join(root, ROUNDS))
    r_anchor = "    '.bak_pycode',\n"
    once(rounds, r_anchor, ROUNDS)
    out[os.path.join(root, ROUNDS)] = rounds.replace(
        r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    wd = read(os.path.join(root, WD))
    for was, now in (
            ('CONVERTED_N = %d' % CONVERTED_WAS,
             'CONVERTED_N = %d   # F2b, 13 Oct 2026 - this round own suite.'
             '\n# test_surface_deep is NOT released: its borders were the'
             '\n# decision, widening is a separate round.   # (was %d)'
             % (CONVERTED_NOW, CONVERTED_WAS)),
            ('WAITING_N = %d' % WAITING_WAS,
             'WAITING_N = %d   # F2b, 13 Oct 2026 - unchanged. The border '
             'decision\n# is taken, but widening the suite is its own round.'
             '   # (still %d)'
             % (WAITING_NOW, WAITING_WAS)),
            ('CONVERTED_N = %d' % CONVERTED_NOW, 'CONVERTED_N = %d'
             % CONVERTED_NOW)):
        once(wd, was, WD)
        wd = wd.replace(was, now, 1)
    out[os.path.join(root, WD)] = wd

    # THE CEILING DOES NOT MOVE. F2b converts no census - the suite it
    # would have converted is the one it decided not to widen.

    co = read(os.path.join(root, CO))
    a_was = 'ok(len(aliased) == %d,' % ALIAS_WAS
    once(co, a_was, CO)
    nco = co.replace(a_was, 'ok(len(aliased) == %d,' % ALIAS_NOW, 1)
    a_txt = ("'%d file(s) alias it - 25 patchers and 26 suites'"
             " % len(aliased),")
    once(nco, a_txt, CO)
    out[os.path.join(root, CO)] = nco.replace(
        a_txt,
        "'%d file(s) alias it - 26 patchers and 27 suites' % len(aliased),"
        "   # F2b, 13 Oct 2026 - this round own patcher and suite"
        "   # (was 51, 25 and 26)", 1)

    ps = read(os.path.join(root, PS1))
    p_anchor = "    'test_py_code.py'\n)"
    once(ps, p_anchor, PS1)
    nps = ps.replace(
        p_anchor, "    'test_py_code.py',\n    '%s'\n)" % SUITE, 1)
    s_anchor = ("    # -------------------------------------------- "
                "E15, 13 Oct 2026")
    once(nps, s_anchor, PS1)
    nps = nps.replace(
        s_anchor,
        "    # -------------------------------------------- F2b, 13 Oct 2026\n"
        "    # A border is named by the border token. The three that keep\n"
        "    # the surface token are base's switched-off recipe, where the\n"
        "    # edge is MEANT to be the fill - and they are a var() fallback,\n"
        "    # not a plain border, which is how the patcher tells them apart.\n"
        "    @{ File = 'pages\\templates\\home.html'; "
        "Text = 'solid var(--alv-surface-deep)'; "
        "What = 'no page draws a plain border on the panel-wash token'; "
        "Absent = $true; Code = $true }\n"
        + s_anchor, 1)
    blk = nps[nps.index('$sentinels = @('):]
    blk = blk[:blk.index('\n)\n')]
    body = [l.rstrip() for l in blk.split('\n')
            if l.strip() and not l.strip().startswith('#')]
    if body[-1].endswith(','):
        refuse('%s: the last thing in $sentinels ends in a comma - a '
               'ParserError before the closing paren, and the script will '
               'not run AT ALL.' % PS1)
    out[os.path.join(root, PS1)] = nps

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('')
        print('F2b  check only - nothing written')
        print('F2b  would convert %d border use(s) on %d page(s) from the'
              % (N_CONVERT, N_PAGES))
        print('F2b  panel-wash token to the border token - 15 RGB units,')
        print('F2b  1.186:1 to 1.236:1 against paper, invisible either way')
        print('F2b  would leave %d var() fallback(s) alone, all of them in'
              % N_FALLBACK)
        print('F2b  base, where a switched-off control edge is its fill')
        print('F2b  would leave %d non-border use(s) alone' % N_OTHER)
        print('F2b  would NOT widen %s - tried, measured, backed out:' % SD)
        print('F2b  widened it reads CRS backups F2a never had a claim on')
        print('F2b  and its two pins would both need re-deriving')
        print('F2b  WAITING %d -> %d, CONVERTED %d -> %d, ceiling %d -> %d'
              % (WAITING_WAS, WAITING_NOW, CONVERTED_WAS, CONVERTED_NOW,
                 CEILING_WAS, CEILING_NOW))
        print('F2b  %d file(s) would change' % len(out))
        return 0

    for p in sorted(out):
        backup(p)
        write(p, out[p])

    print('')
    print('F2b  %d border use(s) on %d page(s) are named by the border'
          % (N_CONVERT, N_PAGES))
    print('F2b  token now. 15 RGB units; 1.186:1 to 1.236:1 against paper.')
    print('F2b  Invisible either way - what changes is that retuning one')
    print('F2b  line of base retunes the right set of things.')
    print('F2b  base.html IS NOT TOUCHED. Its only three border uses are')
    print('F2b  the switched-off recipe, where fill and edge are the SAME')
    print('F2b  expression on purpose, and the patcher refuses them by')
    print('F2b  shape rather than by page name.')
    print('F2b  %s is NOT widened. Tried, measured, backed out: widened' % SD)
    print('F2b  it reads CRS backups F2a never had a claim on - 6 phantom')
    print('F2b  backgrounds and 15 phantom borders - and BL-2 scoped reader')
    print('F2b  fixes those but moves both its pins. A second round inside')
    print('F2b  someone else suite. Its held reason is rewritten instead,')
    print('F2b  to name what actually holds it. WAITING stays at %d.'
          % WAITING_NOW)
    print('F2b  CONVERTED %d -> %d, ceiling %d -> %d'
          % (CONVERTED_WAS, CONVERTED_NOW, CEILING_WAS, CEILING_NOW))
    print('F2b  %d file(s) changed' % len(out))
    print('F2b  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
