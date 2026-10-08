# -*- coding: utf-8 -*-
"""apply_edit_ink.py - Section B round B-4b, 8 Oct 2026.

ONE DECLARATION, AND THE GATE THAT SHOULD HAVE CAUGHT IT.

B-4 converted .btn-edit:hover on view_recipe.html. The fill moved from
Bootstrap's #e0a800 to --alv-warn (#8e6207) and the #000 ink STAYED
WHERE IT WAS, so the pair went from 9.77:1 to 3.90:1 - below AA, on a
hover state that ships. One failure in 26 pairs.

    .btn-edit:hover { background: var(--alv-warn); color: #000; }
    .btn-edit:hover { background: var(--alv-warn); color: var(--alv-on-accent); }

5.38:1, and it is base's own pairing: .badge-warning is white on
--alv-warn and has been since B-3.

=====================================================================
WHY THE GATE DID NOT SEE IT, AND WHAT IS BEING DONE ABOUT IT
=====================================================================

B-4's gate checked that every INK conversion improved contrast. It
never checked a FILL conversion against the ink already sitting on it.
That is not a bug in one check, it is a whole class the house had no
instrument for: a rule's colour is a PAIR, and a round that moves half
a pair has changed the pair.

So B-4b also lays down test_pair_contrast.py - a census of EVERY rule
in the tree that sets both a background and a colour, with the pairs
below AA pinned by name. 701 pairs; 54 read below 4.5:1.

    21  disabled or inactive. WCAG 1.4.3 exempts an inactive control,
        and these are genuinely inactive - :disabled, [disabled],
        aria-disabled, .is-disabled, .inactive, placeholders.

    33  LIVE, and this round takes one of them. The remaining 32 are
        pinned BY NAME, not just counted, so a later round cannot add
        one by quietly swapping a different one out.

THE 32 ARE NOT ANONYMOUS DEBT. Every one has an owner already:

    17  the house accent on a house tint. --alv-accent #0e7c8b on
        --alv-accent-soft #e4f3f5 is 4.31:1, on --alv-line-soft
        #f1f3f5 is 4.42:1, on --alv-surface-deep #e9ecef is 4.14:1.
        THIS IS A BASE DECISION, NOT SEVENTEEN PAGE FIXES: the house
        pairs its own accent with its own tint and the pairing misses
        AA by a tenth. --alv-accent-ink #0a5e6a on #e4f3f5 is 6.24:1.
        Logged for him, not taken here.

     7  Bootstrap brights - #ffc107 and #fd7e14 under white. Decision
        4, round B-7.

     2  #e65100 on --alv-warn-soft, the recipe theme. Round RC-2.

     6  strays with no family yet: #ccc on white, #adb5bd on
        --alv-surface twice, #41535c on --alv-neutral in base,
        #0a5e6a on --alv-accent, #8a979d on --alv-line-soft.

=====================================================================
THE THIRD COPY
=====================================================================

pair_table() now exists in apply_neutrals.py and here. A THIRD round
needing it is the signal to promote it into alv_cssrules.py - which is
in alv_impact.WIDE, so that promotion owes a full sweep and is a round
of its own, not a line smuggled into a one-declaration fix.

FILES: view_recipe.html (+ .bak_editink), alv_rounds.py, the PS1
$suites, alv_impact.py, and the new test_pair_contrast.py.
"""
import collections
import os
import re
import sys

SUFFIX = '.bak_editink'
MARK = 'B-4b, 8 Oct 2026'
SUITE_NAME = 'test_pair_contrast.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_cssrules as R                                   # noqa: E402
import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
CHECK = False

PAGE = 'view_recipe.html'
OLD = 'background: var(--alv-warn); color: #000;'
NEW = 'background: var(--alv-warn); color: var(--alv-on-accent);'

EXPECT_PAIRS = 701
EXPECT_LIVE_BEFORE = 33
EXPECT_LIVE_AFTER = 32
EXPECT_DISABLED = 21

# WCAG 1.4.3 exempts text that is part of an inactive user interface
# component. These are the selector marks that say a rule is one.
INACTIVE = re.compile(r'disabled|aria-disabled|is-disabled|\.inactive|'
                      r'placeholder|readonly', re.I)


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


def rgb(h):
    h = h.lstrip('#')
    if len(h) in (4, 8):
        h = h[:len(h) // 4 * 3]
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def lum(h):
    c = rgb(h)
    if not c:
        return None

    def f(x):
        x /= 255.0
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2])


def contrast(a, b):
    la, lb = lum(a), lum(b)
    if la is None or lb is None:
        return None
    hi, lo = max(la, lb), min(la, lb)
    return (hi + .05) / (lo + .05)


def base_tokens():
    """Every --alv-* base declares on :root. Base carries them in TWO
    separate rules and a map built from the first alone is six short."""
    code = T.code_only(read(T.path_of('base.html')))
    out = {}
    for a, b in R.style_spans(code):
        for sel, ba, bb, _x, _y in R.rule_spans(code, a, b):
            if ':root' not in sel:
                continue
            for k, v in re.findall(r'(--alv-[\w-]+)\s*:\s*([^;}]+)',
                                   code[ba:bb]):
                out[k] = v.strip()
    return out


def resolve(v, tok, depth=0):
    """The hex a declaration's value ends up as - a literal, or a token
    chased through however many hops of var() base uses. --alv-info is
    var(--alv-accent), so one hop is not enough."""
    if not v or depth > 6:
        return None
    m = re.search(r'var\((--[\w-]+)\)', v)
    if m:
        return resolve(tok.get(m.group(1)), tok, depth + 1)
    m = re.search(r'#[0-9a-fA-F]{3,8}(?![\w-])', v)
    return m.group(0) if m else None


def decls_of(code, ba, bb):
    d = {}
    for ch in code[ba:bb].split(';'):
        if ':' in ch:
            k = R.norm(ch.partition(':')[0]).lower()
            if k and not k.startswith('--'):
                d[k] = R.norm(ch.partition(':')[2])
    return d


def pair_table(code, tok):
    """{selector: (background, colour)} for every rule setting both.

    Keyed on the BODY span, because a grouped selector gives the same
    body back once per name and counting per name double-counts it -
    which is how IM-1 read base's 73 !important as 122.
    """
    out = {}
    for a, b in R.style_spans(code):
        bodies = collections.OrderedDict()
        for sel, ba, bb, _x, _y in R.rule_spans(code, a, b):
            bodies.setdefault((ba, bb), []).append(sel)
        for (ba, bb), sels in bodies.items():
            d = decls_of(code, ba, bb)
            bg = resolve(d.get('background-color') or d.get('background'), tok)
            ink = resolve(d.get('color'), tok)
            if bg and ink:
                for s in sels:
                    out[s] = (bg, ink)
    return out


def census(override=None):
    """(all_pairs, live_below_AA, inactive_below_AA) over the whole tree.

    `override` maps a full path to replacement text, so the round can
    measure what it is ABOUT to write before it writes it. A patcher
    verifies, then writes.
    """
    tok = base_tokens()
    override = override or {}
    n = 0
    live, dead = [], []
    for p in sorted(T.templates()):
        code = T.code_only(override.get(p) or read(p))
        for sel, (bg, ink) in pair_table(code, tok).items():
            cr = contrast(bg, ink)
            if cr is None:
                continue
            n += 1
            if cr < 4.5:
                row = (T.rel(p), sel.split(' && ')[-1], round(cr, 2), bg, ink)
                (dead if INACTIVE.search(sel) else live).append(row)
    return n, sorted(live, key=lambda r: r[2]), sorted(dead, key=lambda r: r[2])


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('B-4b  already applied')
        return 1 if CHECK else 0

    path = T.path_of(PAGE)
    raw = read(path)
    if raw.count(fit(raw, OLD)) != 1:
        raise SystemExit('B-4b: the .btn-edit:hover declaration matched %d '
                         'time(s) in %s, not once. B-4 wrote it and nothing '
                         'since should have moved it.'
                         % (raw.count(fit(raw, OLD)), PAGE))
    out = raw.replace(fit(raw, OLD), fit(raw, NEW), 1)

    # ---- the pair itself -------------------------------------------
    tok = base_tokens()
    if '--alv-on-accent' not in tok:
        raise SystemExit('B-4b: base declares no --alv-on-accent. A var() '
                         'naming a token base has not got is an invalid '
                         'declaration and the colour falls back silently.')
    was = contrast(tok['--alv-warn'], '#000000')
    now = contrast(tok['--alv-warn'], tok['--alv-on-accent'])
    print('B-4b  .btn-edit:hover  %.2f:1 -> %.2f:1' % (was, now))
    if now < 4.5:
        raise SystemExit('B-4b: the replacement reads %.2f:1, which is the '
                         'fault it is meant to fix' % now)
    if was >= 4.5:
        raise SystemExit('B-4b: the pair already reads %.2f:1. Somebody has '
                         'fixed this and the round has nothing to do.' % was)

    # ---- and the whole-tree census it is laying down ---------------
    n0, live0, dead0 = census()
    n1, live1, dead1 = census({path: out})
    print('B-4b  %d fill/ink pairs tree-wide' % n0)
    print('B-4b  below AA, live:     %d -> %d' % (len(live0), len(live1)))
    print('B-4b  below AA, inactive: %d  (WCAG 1.4.3 exempts these)'
          % len(dead0))
    if n0 != EXPECT_PAIRS or n1 != EXPECT_PAIRS:
        raise SystemExit('B-4b: %d/%d pairs, expected %d. The census moved '
                         'under this round and it will not pin a number it '
                         'has not measured.' % (n0, n1, EXPECT_PAIRS))
    if len(live0) != EXPECT_LIVE_BEFORE or len(live1) != EXPECT_LIVE_AFTER:
        raise SystemExit('B-4b: live below AA %d -> %d, expected %d -> %d'
                         % (len(live0), len(live1), EXPECT_LIVE_BEFORE,
                            EXPECT_LIVE_AFTER))
    if len(dead0) != EXPECT_DISABLED or len(dead1) != EXPECT_DISABLED:
        raise SystemExit('B-4b: %d inactive pairs below AA, expected %d - '
                         'this round touches no disabled state'
                         % (len(dead0), EXPECT_DISABLED))
    gone = [r for r in live0 if r not in live1]
    if len(gone) != 1 or gone[0][1] != '.btn-edit:hover':
        raise SystemExit('B-4b: the round removed %s from the failing list, '
                         'and the only thing it is allowed to remove is '
                         '.btn-edit:hover' % ([r[1] for r in gone],))

    if not CHECK:
        backup(path)
        write(path, out)

        # ---- alv_rounds.ROUNDS -------------------------------------
        NOTE = """    # B-4b, 8 Oct 2026 - one declaration, and the instrument that
    # should have caught it. B-4 moved .btn-edit:hover's FILL to
    # --alv-warn and left the #000 ink where it was: 9.77:1 became
    # 3.90:1 on a hover state that ships. The ink is now
    # --alv-on-accent at 5.38:1, which is base's own .badge-warning
    # pairing.
    #
    # A rule's colour is a PAIR, and a round that moves half a pair
    # has changed the pair. B-4's gate checked ink conversions and
    # never fill conversions against their companion ink, so it could
    # not see this. test_pair_contrast.py is the census that can: 701
    # pairs tree-wide, 54 below AA - 21 of them inactive controls,
    # which WCAG 1.4.3 exempts, and 32 live ones PINNED BY NAME so a
    # later round cannot add one by swapping a different one out.
    '%s',
""" % SUFFIX
        for anchor in ("    '.bak_amber',\n]", "    '.bak_pmlabels',\n]"):
            if rounds.count(fit(rounds, anchor)) == 1:
                rounds = rounds.replace(fit(rounds, anchor),
                                        fit(rounds, anchor[:-2] + NOTE + ']'),
                                        1)
                break
        else:
            raise SystemExit('B-4b: could not find the tail of ROUNDS')
        backup(ROUNDS)
        write(ROUNDS, rounds)

        # ---- the PS1 $suites list ----------------------------------
        PS_NOTE = """    # B-4b, 8 Oct 2026 - the fill/ink PAIR census. Section 2 is
    # the one declaration this round fixed; section 3 pins the 32
    # live pairs still below AA by name, each against the round
    # that owns it; section 4 names the 21 inactive ones and says
    # why WCAG exempts them.
    '%s'
)""" % SUITE_NAME
        for anchor in ("    'test_amber.py'\n)",
                       "    'test_passport_mobile.py'\n)"):
            if ps.count(fit(ps, anchor)) == 1:
                ps = ps.replace(fit(ps, anchor),
                                fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
                break
        else:
            raise SystemExit('B-4b: could not find the tail of $suites')
        backup(PS1)
        write(PS1, ps)

        # ---- alv_impact.COUNTERS -----------------------------------
        # It counts every rule in every template. A point round
        # anywhere can move it, so it belongs on the list that gets
        # run whatever else changed - the list CR-1 and IM-1 both
        # forgot to join, which is how B-4's push came to fail.
        IMP = os.path.join(ROOT, 'alv_impact.py')
        isrc = read(IMP)
        OLD_C = "    'test_important_base.py',    # !important, whole tree\n]"
        NEW_C = ("    'test_important_base.py',    # !important, whole tree\n"
                 "    # B-4b, 8 Oct 2026 - adding itself: it counts the\n"
                 "    # fill/ink pairs of every rule in every template.\n"
                 "    'test_pair_contrast.py',     # fill/ink pairs, whole tree\n"
                 "]")
        if isrc.count(fit(isrc, OLD_C)) != 1:
            raise SystemExit('B-4b: the tail of COUNTERS matched %d time(s), '
                             'not once' % isrc.count(fit(isrc, OLD_C)))
        isrc = isrc.replace(fit(isrc, OLD_C), fit(isrc, NEW_C), 1)
        import ast as _ast
        try:
            _ast.parse(isrc)
        except SyntaxError as e:
            raise SystemExit('B-4b: alv_impact.py would not parse - %s' % e)
        backup(IMP)
        write(IMP, isrc)
        print('B-4b  alv_impact.COUNTERS +1 (it adds itself)')

    if CHECK:
        print('B-4b  NOT APPLIED')
        return 1
    print('B-4b  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
