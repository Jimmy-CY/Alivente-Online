"""B-2 - THE FOUR NEUTRALS, AND THIS ONE MOVES PIXELS.

   B-1 took tier A: 957 literals that were ALREADY the byte-identical
   value of the token replacing them. Its whole argument was that it
   could not move a pixel, and the gate proved that by resolving values
   rather than by looking.

   THIS ROUND CANNOT BORROW THAT ARGUMENT. Tier B is 1,101 uses within 25
   RGB units of a token, and B-2 is the four neutrals inside it - 758
   uses on 93 pages, each moving between 9 and 25 units:

       #6c757d  ink/fill/line  277  -> --alv-ink-soft      22.1
       #dee2e6  line           201  -> --alv-line           8.8
       #dee2e6  fill             3  -> --alv-surface-deep  17.4
       #2c3e50  ink/fill       168  -> --alv-ink           24.9
       #495057  ink/fill       109  -> --alv-ink-strong     9.9

   SO THE GATE IS A BOUNDED ONE, not an equality. Every substitution must
   move by EXACTLY the distance this file records, to a tenth of a unit,
   and no further. If somebody changes --alv-ink-soft tomorrow this round
   refuses to run rather than quietly moving 277 declarations somewhere
   nobody looked at. "Within 25" would not do that; "exactly 22.1" does.

   DEMETRI LOOKED FIRST, at both widths, 6 Oct 2026. Two of the four get
   measurably more readable and neither change is visible:

       #6c757d  4.69:1 -> 5.53:1 on paper   - and 4.69 clears the AA
                                              floor for normal text by
                                              four hundredths, on 229
                                              uses of which a third are
                                              set at 11px or 12px
       #2c3e50 10.98:1 -> 12.95:1

   THE BORDERS WERE THE ARGUMENT. #dee2e6 -> --alv-line makes 201 borders
   FAINTER, 1.30:1 down to 1.24:1 against paper. Demetri chose to include
   them, because --alv-line is already what every base-styled table draws
   with: the change makes these 93 pages AGREE with base rather than
   disagree, and afterwards one value moves every border in the app at
   once instead of half of them. That is the decision; this file is where
   it is written down.

   WHAT IS NOT HERE: #adb5bd, #ced4da and #000000 are tier C - a real
   colour change - and the rest of tier B is B-2b, by family.

   FILES: 93 templates.                      [test_colour_neutrals.py]
"""
import os
import re
import sys

import alv_tree as T
import alv_cssrules as R

from apply_colour_tokens import as_colour, role_of, root_values

SUFFIX = '.bak_coltok2'

# (colour, role) -> (token, the move, to a tenth of an RGB unit)
#
# THE MOVE IS PART OF THE MAP, and that is the difference between this
# round and B-1. B-1 asserted equality, which needs no number. Here the
# number IS the claim: this substitution moves the pixel 22.1 units and
# not 23, and if base changes the round stops.
MAP = {
    ('#6c757d', 'INK'): ('--alv-ink-soft', 22.1),
    ('#6c757d', 'FILL'): ('--alv-ink-soft', 22.1),
    ('#6c757d', 'LINE'): ('--alv-ink-soft', 22.1),
    ('#dee2e6', 'LINE'): ('--alv-line', 8.8),
    ('#dee2e6', 'FILL'): ('--alv-surface-deep', 17.4),
    ('#2c3e50', 'INK'): ('--alv-ink', 24.9),
    ('#2c3e50', 'FILL'): ('--alv-ink', 24.9),
    ('#495057', 'INK'): ('--alv-ink-strong', 9.9),
    ('#495057', 'FILL'): ('--alv-ink-strong', 9.9),
}

EXPECT_CUTS = 758
EXPECT_PAGES = 93

# No substitution in this round may move further than this. The map's own
# numbers are all below it; the ceiling is here so that a change to base
# which happened to keep a pair inside the map still cannot smuggle a
# tier-C move in under a tier-B heading.
CEILING = 25.0

MARK = 'B-2, 6 Oct 2026'

NOTE = ('    /* %s - %d literal(s) on this page became a var(), and\n'
        '       unlike B-1 these MOVED: between 9 and 25 RGB units, which\n'
        '       is below what an eye reads as a different colour and above\n'
        '       nothing. Demetri looked at all four side by side at phone\n'
        '       and desktop width before this ran.\n'
        '       Two of them read BETTER: the muted grey goes 4.69:1 to\n'
        '       5.53:1 on paper and the heading ink 10.98 to 12.95.\n'
        '       The borders go the other way, 1.30 to 1.24, and that was\n'
        '       the decision - they now agree with base.   [B-2 tier B] */\n')

LIT = re.compile(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b'
                 r'|rgba?\([^()]*\)', re.I)


def dist(a, b):
    def rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return sum((x - y) ** 2 for x, y in zip(rgb(a), rgb(b))) ** 0.5


def cuts_for(text):
    """[(start, end, literal, prop, token, selector), ...], by offset."""
    out = []
    for a, b in R.style_spans(text):
        seen = set()
        for sel, ba, bb, ra, rb in R.rule_spans(text, a, b):
            # DR-2b's trap: the same body, once per grouped selector.
            if (ba, bb) in seen:
                continue
            seen.add((ba, bb))
            pos = ba
            for chunk in text[ba:bb].split(';'):
                start = pos
                pos += len(chunk) + 1
                if ':' not in chunk or '{' in chunk or '}' in chunk:
                    continue
                prop, val = chunk.split(':', 1)
                role = role_of(prop)
                if not role:
                    continue
                voff = start + len(prop) + 1
                for m in LIT.finditer(val):
                    col = as_colour(m.group(0))
                    if col is None:
                        continue
                    hit = MAP.get((col, role))
                    if hit:
                        out.append((voff + m.start(), voff + m.end(),
                                    m.group(0), prop.strip(), hit[0], sel))
    return sorted(out)


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    if '\r\n' in text:
        return block.replace('\r\n', '\n').replace('\n', '\r\n')
    return block.replace('\r\n', '\n')


def prove_moves():
    """EXACTLY THE MOVE THIS FILE RECORDS, and no further."""
    bp = T.path_of('base.html')
    vals, ats = root_values(read(bp))

    for (col, role), (tok, want) in sorted(MAP.items()):
        if tok not in vals:
            raise SystemExit('B-2: %s is not declared in base\'s :root'
                             % tok)
        got = as_colour(vals[tok].strip())
        if got is None:
            raise SystemExit('B-2: %s reads %r, which is not a colour'
                             % (tok, vals[tok].strip()))
        d = dist(col, got)
        if abs(d - want) > 0.05:
            raise SystemExit(
                'B-2: %s %s -> %s now moves %.1f units, not the %.1f this '
                'round was measured and looked at with. Base has changed '
                'since; re-measure and show the renders again before '
                'moving 758 declarations.' % (col, role, tok, d, want))
        if d > CEILING:
            raise SystemExit('B-2: %s %s -> %s moves %.1f, over the %.1f '
                             'ceiling - that is a tier C change wearing a '
                             'tier B label' % (col, role, tok, d, CEILING))
    return len(vals)


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # B-1 FIRST. This round leaves the tree it left, and its exemption -
    # the twelve standalone templates - is the same exemption.
    bt = read(T.path_of('base.html'))
    if 'B-1, 5 Oct 2026' not in bt:
        raise SystemExit('B-2: B-1 has not been applied - tier B builds on '
                         'the tree tier A leaves')

    ntok = prove_moves()

    stand = set(T.standalone())
    plan = {}
    for p in T.templates():
        name = T.rel(p).replace(os.sep, '/')
        if name in stand:
            continue
        raw = read(p)
        if MARK in raw:
            continue
        c = cuts_for(T.code_only(raw))
        if c:
            plan[name] = (p, raw, c)

    total = sum(len(v[2]) for v in plan.values())

    if total == 0:
        done = sum(1 for p in T.templates() if MARK in read(p))
        print('B-2  cuts  : 0')
        print('B-2  pages : %d already carry the note' % done)
        print('B-2  applied' if check else 'B-2  ok')
        return 0

    if total != EXPECT_CUTS or len(plan) != EXPECT_PAGES:
        raise SystemExit('B-2: measured %d cut(s) on %d page(s), the map '
                         'says %d on %d - the tree has changed since it '
                         'was measured and looked at'
                         % (total, len(plan), EXPECT_CUTS, EXPECT_PAGES))

    for name, (p, raw, c) in sorted(plan.items()):
        spans = sorted(set((a, b) for a, b, _l, _pr, _t, _s in c),
                       reverse=True)
        if len(spans) != len(c):
            raise SystemExit('B-2: %s produced %d cut(s) over %d distinct '
                             'span(s)' % (name, len(c), len(spans)))
        last = None
        for a, b in spans:
            if last is not None and b > last:
                raise SystemExit('B-2: overlapping cuts on %s at %d-%d'
                                 % (name, a, b))
            last = a

        text = raw
        for a, b, lit, prop, tok, sel in sorted(c, reverse=True):
            if text[a:b] != lit:
                raise SystemExit('B-2: %s at %d reads %r, not %r'
                                 % (name, a, text[a:b], lit))
            text = text[:a] + 'var(%s)' % tok + text[b:]

        again = cuts_for(T.code_only(text))
        if again:
            raise SystemExit('B-2: %s still holds %d neutral literal(s) '
                             'after the rewrite' % (name, len(again)))

        # B-1's lesson, and it cost a revert of 102 files: style_spans has
        # no comment awareness, and lease_renewal_report.html carries a
        # CSS comment that MENTIONS a style tag. Read raw, the note goes
        # into the middle of that sentence; nothing measurable changes,
        # every count passes, and one render four modules away notices.
        sp = R.style_spans(T.code_only(text))
        at = sp[-1][0]
        note = fit(text, NOTE % (MARK, len(c)))
        text = text[:at] + note + text[at:]
        if T.code_only(text)[at:at + len(note)].strip():
            raise SystemExit('B-2: the note on %s did not land in a style '
                             'block - it is live CSS at %d' % (name, at))

        if not check:
            backup(p)
            write(p, text)

    print('B-2  moves proved against base : %d of %d' % (len(MAP), ntok))
    print('B-2  cuts                      : %d' % total)
    print('B-2  pages                     : %d' % len(plan))
    print('B-2  largest move              : %.1f of %.1f allowed'
          % (max(w for _t, w in MAP.values()), CEILING))
    if check:
        print('B-2  NOT APPLIED')
        return 1
    print('B-2  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
