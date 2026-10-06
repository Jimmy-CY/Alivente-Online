"""B-2b - THE TAIL OF TIER B, 342 USES IN FIVE FAMILIES.

   B-2 took the four neutrals that are most of tier B by weight: 758 uses
   of four colours. THIS IS EVERYTHING ELSE INSIDE 25 UNITS - 105 pairs
   across 67 pages, and the shape of it is the point:

       neutral  122 uses   53 pairs    greys nobody chose twice the same way
       warn      92 uses   12 pairs    #856404 and Bootstrap's alert amber
       good      43 uses   10 pairs    #155724 and the success panels
       bad       38 uses    9 pairs    #f8d7da and the danger panels
       accent    34 uses   21 pairs    21 ways of writing a pale teal
       blue      13 uses    1 pair     #e3f2fd, a Material info panel

   TWENTY-ONE WAYS OF WRITING A PALE TEAL, and fifty-three greys. That is
   what a long tail IS: not a programme nobody got to, but the same
   decision made separately by whoever was writing that page that day.
   #e7f5f8, #e6f6f8, #e8f6f5, #e0f7fa, #eef7f9, #f1f8fa, #f4f9fb,
   #f4fbfa, #d4ecf2 - nine spellings of --alv-accent-soft, fourteen uses
   between them, and no two pages agreeing.

   THE GATE IS B-2'S, UNCHANGED: every substitution must move by exactly
   the distance this file records, to a tenth of a unit, under a 25.0
   ceiling. The map is bigger; the proof is the same size.

   FOUR ENTRIES WERE CORRECTED BY HAND, and they are the reason a
   classifier produces a DRAFT rather than a map:

     #ecf0f1  Flat-UI's "clouds" grey. Five RGB units wide, but its hue
              reads 192 - just outside the 200-245 band that says
              "Bootstrap grey" - so the classifier called it a pale teal
              and aimed it at --alv-accent-soft. A colour five units
              wide is not a colour. -> --alv-surface-deep, 5.4.
     #e8f4ff  Pale blues, 23 units wide, which the same band swallowed
     #e8f4fd  as greys. Both are NEARER --alv-accent-soft than the grey
              they were pointed at, and the house has no other pale
              blue. -> --alv-accent-soft.
     #f8f9fa  DROPPED, not corrected. As a LINE on one page it is the
              page's own background colour - a border deliberately
              invisible. --alv-line-soft is the right line token and
              would make it VISIBLE, which is a change of appearance on
              a decision nobody has made. One use; it waits for a
              person. [generate_lease_agreement.html]

   FILES: 67 templates.                       [test_colour_tail.py]
"""
import os
import re
import sys

import alv_tree as T
import alv_cssrules as R

from apply_colour_tokens import as_colour, role_of, root_values
from apply_colour_neutrals import dist, LIT

SUFFIX = '.bak_coltok3'

# (colour, role) -> (token, the move, to a tenth of an RGB unit)
MAP = {
    # --- neutral ---------------------------------------------------
    ('#f0f0f0', 'LINE'): ('--alv-line-soft', 5.9),
    ('#343a40', 'INK'): ('--alv-ink', 20.3),
    ('#212529', 'INK'): ('--alv-ink', 24.2),
    ('#5a6268', 'FILL'): ('--alv-ink-soft', 14.2),
    ('#7f8c8d', 'INK'): ('--alv-ink-faint', 22.3),
    ('#868e96', 'INK'): ('--alv-ink-faint', 12.1),
    ('#dddddd', 'LINE'): ('--alv-line', 18.1),
    ('#f0f2ff', 'FILL'): ('--alv-line-soft', 10.1),
    ('#343a40', 'FILL'): ('--alv-ink', 20.3),
    ('#e0e0e0', 'LINE'): ('--alv-line', 13.2),
    ('#eeeeee', 'LINE'): ('--alv-surface-deep', 5.5),
    ('#fafafa', 'FILL'): ('--alv-surface', 2.2),
    ('#fbfbfc', 'FILL'): ('--alv-surface', 4.1),
    ('#1f2937', 'LINE'): ('--alv-ink', 12.2),
    ('#545b62', 'LINE'): ('--alv-ink-soft', 24.4),
    ('#55606b', 'LINE'): ('--alv-ink-soft', 14.9),
    ('#666666', 'INK'): ('--alv-ink-soft', 17.7),
    ('#8a939b', 'INK'): ('--alv-ink-faint', 4.5),
    ('#95a5a6', 'INK'): ('--alv-ink-faint', 19.9),
    ('#9aa0a6', 'INK'): ('--alv-ink-faint', 20.4),
    ('#dfe4e8', 'LINE'): ('--alv-line', 6.0),
    ('#e8eaec', 'FILL'): ('--alv-surface-deep', 3.7),
    ('#e8eaec', 'LINE'): ('--alv-surface-deep', 3.7),
    ('#e8f4ff', 'FILL'): ('--alv-accent-soft', 10.8),   # family corrected by hand
    ('#f1f1f1', 'FILL'): ('--alv-line-soft', 4.5),
    ('#f8f9ff', 'FILL'): ('--alv-surface', 5.0),
    ('#fafbfc', 'FILL'): ('--alv-surface', 3.5),
    ('#1f2937', 'FILL'): ('--alv-ink', 12.2),
    ('#343a40', 'LINE'): ('--alv-ink', 20.3),
    ('#41464b', 'INK'): ('--alv-ink-strong', 21.4),
    ('#4a5560', 'INK'): ('--alv-ink-strong', 10.0),
    ('#525659', 'FILL'): ('--alv-ink-strong', 17.5),
    ('#546e7a', 'FILL'): ('--alv-ink-soft', 10.3),
    ('#555555', 'INK'): ('--alv-ink-strong', 21.3),
    ('#7f8c8d', 'LINE'): ('--alv-ink-faint', 22.3),
    ('#999999', 'INK'): ('--alv-ink-faint', 15.7),
    ('#dae0e5', 'LINE'): ('--alv-line', 13.0),
    ('#e0e0e0', 'FILL'): ('--alv-surface-deep', 21.2),
    ('#e1e5e9', 'LINE'): ('--alv-line', 3.7),
    ('#e2e3e5', 'FILL'): ('--alv-surface-deep', 15.2),
    ('#e2e4e6', 'FILL'): ('--alv-surface-deep', 13.9),
    ('#e2e6ea', 'FILL'): ('--alv-surface-deep', 10.5),
    ('#e5e7eb', 'LINE'): ('--alv-line', 2.4),
    ('#e8e8e8', 'FILL'): ('--alv-surface-deep', 8.1),
    ('#e8f4fd', 'FILL'): ('--alv-accent-soft', 9.0),   # family corrected by hand
    ('#eef0f2', 'LINE'): ('--alv-line-soft', 5.2),
    ('#f0f0f0', 'FILL'): ('--alv-line-soft', 5.9),
    ('#f0f8ff', 'FILL'): ('--alv-surface', 9.5),
    ('#f0f9ff', 'FILL'): ('--alv-surface', 9.4),
    ('#f1f6f9', 'FILL'): ('--alv-line-soft', 5.0),
    ('#f3f3f3', 'LINE'): ('--alv-line-soft', 2.8),
    ('#f5f5f5', 'FILL'): ('--alv-line-soft', 4.5),

    # --- warn ------------------------------------------------------
    ('#856404', 'INK'): ('--alv-warn', 9.7),
    ('#fff3cd', 'FILL'): ('--alv-warn-soft', 16.1),
    ('#fffbf0', 'FILL'): ('--alv-warn-soft', 20.7),
    ('#ecd9a8', 'LINE'): ('--alv-warn-line', 11.7),
    ('#fff8e1', 'FILL'): ('--alv-warn-soft', 6.7),
    ('#fff8e6', 'FILL'): ('--alv-warn-soft', 10.5),
    ('#fdf8f0', 'FILL'): ('--alv-warn-soft', 19.6),
    ('#6c5400', 'INK'): ('--alv-warn-ink', 11.4),
    ('#fef5e7', 'FILL'): ('--alv-warn-soft', 10.2),
    ('#fff3e0', 'FILL'): ('--alv-warn-soft', 3.6),
    ('#6b5b12', 'INK'): ('--alv-warn-ink', 21.4),
    ('#fcf8e3', 'FILL'): ('--alv-warn-soft', 7.9),

    # --- good ------------------------------------------------------
    ('#155724', 'INK'): ('--alv-good-ink', 19.0),
    ('#f0fff4', 'FILL'): ('--alv-good-soft', 16.9),
    ('#e8f5e9', 'FILL'): ('--alv-good-soft', 3.7),
    ('#c3e6cb', 'LINE'): ('--alv-good-line', 7.5),
    ('#d4e4d4', 'LINE'): ('--alv-good-line', 22.5),
    ('#e9f7ef', 'FILL'): ('--alv-good-soft', 5.2),
    ('#f0fbf4', 'FILL'): ('--alv-good-soft', 14.6),
    ('#b7e0c8', 'LINE'): ('--alv-good-line', 9.4),
    ('#c8e6c9', 'LINE'): ('--alv-good-line', 11.5),
    ('#c8e8d4', 'LINE'): ('--alv-good-line', 13.9),

    # --- bad -------------------------------------------------------
    ('#f8d7da', 'FILL'): ('--alv-bad-soft', 24.4),
    ('#fff5f5', 'FILL'): ('--alv-bad-soft', 16.8),
    ('#bd2130', 'LINE'): ('--alv-bad', 21.2),
    ('#a71d2a', 'INK'): ('--alv-bad', 19.2),
    ('#fdecea', 'FILL'): ('--alv-bad-soft', 3.0),
    ('#fed7d7', 'LINE'): ('--alv-bad-line', 19.2),
    ('#fdecee', 'FILL'): ('--alv-bad-soft', 5.7),
    ('#842029', 'INK'): ('--alv-bad-ink', 21.3),
    ('#f5c6cb', 'LINE'): ('--alv-bad-line', 8.5),

    # --- accent ----------------------------------------------------
    ('#e7f5f8', 'FILL'): ('--alv-accent-soft', 4.7),
    ('#d1ecf1', 'FILL'): ('--alv-accent-soft', 20.6),
    ('#b8e2ea', 'LINE'): ('--alv-accent-line', 22.4),
    ('#e6f6f8', 'FILL'): ('--alv-accent-soft', 4.7),
    ('#e6f7ff', 'FILL'): ('--alv-accent-soft', 11.0),
    ('#00838f', 'INK'): ('--alv-accent', 16.2),
    ('#0c5460', 'LINE'): ('--alv-accent-ink', 14.3),
    ('#0c5460', 'FILL'): ('--alv-accent-ink', 14.3),
    ('#0c5460', 'INK'): ('--alv-accent-ink', 14.3),
    ('#0f766e', 'LINE'): ('--alv-accent-ink', 24.8),
    ('#0f766e', 'INK'): ('--alv-accent-ink', 24.8),
    ('#17677a', 'INK'): ('--alv-accent-ink', 22.5),
    ('#b7e0dd', 'LINE'): ('--alv-accent-line', 17.0),
    ('#d4ecf2', 'FILL'): ('--alv-accent-soft', 17.7),
    ('#e0f7fa', 'FILL'): ('--alv-accent-soft', 7.5),
    ('#e8f6f5', 'FILL'): ('--alv-accent-soft', 5.0),
    ('#ecf0f1', 'FILL'): ('--alv-surface-deep', 5.4),   # family corrected by hand
    ('#eef7f9', 'FILL'): ('--alv-accent-soft', 11.5),
    ('#f1f8fa', 'FILL'): ('--alv-accent-soft', 14.8),
    ('#f4f9fb', 'FILL'): ('--alv-accent-soft', 18.1),
    ('#f4fbfa', 'FILL'): ('--alv-accent-soft', 18.6),

    # --- blue ------------------------------------------------------
    ('#e3f2fd', 'FILL'): ('--alv-accent-soft', 8.1),
}

# A PAGE CAN KEEP A COLOUR BY DECISION, and one does.
#
# fsr_details.html spells #ecd9a8 once, and test_fsr_palette ALLOWS it
# by name: "the Notify round's page-local warn tint, decided last night
# with a single asker". --alv-warn-line is #ecd39e - 11.7 units away,
# which is a different tint. Converting it would quietly overrule a
# decision Demetri made, and the suite that records the decision caught
# it in the sweep.
#
# THE OTHER FIVE USES OF THAT SAME COLOUR ARE CONVERTED, four of them
# in base.html - where #ecd9a8 sits four times while base's own
# --alv-warn-line says #ecd39e. base disagreed with its own token, in
# its own file. It does not any more.
KEEP = {('fsr_details.html', '#ecd9a8')}

EXPECT_CUTS = 341
EXPECT_PAGES = 67
CEILING = 25.0

MARK = 'B-2b, 6 Oct 2026'

NOTE = ('    /* %s - %d literal(s) on this page became a var().\n'
        '       The tail of tier B: everything within 25 RGB units of a\n'
        '       token that was not one of B-2 four neutrals. Twenty-one\n'
        '       spellings of a pale teal, fifty-three greys, and the\n'
        '       Bootstrap alert colours. Same bounded gate as B-2: each\n'
        '       one moves by exactly the distance the map records, or\n'
        '       the round refuses to run.               [B-2b tier B] */\n')

def cuts_for(text, name=''):
    """[(start, end, literal, prop, token, selector), ...], by offset.

    `name` is the page being read, because KEEP is per page: a colour
    one template holds by decision is still drift on the next one."""
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
                    if (name, col) in KEEP:
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
            raise SystemExit('B-2b: %s is not declared in base\'s :root'
                             % tok)
        got = as_colour(vals[tok].strip())
        if got is None:
            raise SystemExit('B-2b: %s reads %r, which is not a colour'
                             % (tok, vals[tok].strip()))
        d = dist(col, got)
        if abs(d - want) > 0.05:
            raise SystemExit(
                'B-2b: %s %s -> %s now moves %.1f units, not the %.1f this '
                'round was measured and looked at with. Base has changed '
                'since; re-measure and show the renders again before '
                'moving 758 declarations.' % (col, role, tok, d, want))
        if d > CEILING:
            raise SystemExit('B-2b: %s %s -> %s moves %.1f, over the %.1f '
                             'ceiling - that is a tier C change wearing a '
                             'tier B label' % (col, role, tok, d, CEILING))
    return len(vals)


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # B-2 FIRST - and through it B-1. This is the tail of the tier B-2
    # took the head of; running it on a tree where the four neutrals are
    # still literals would leave the map measuring a different tree from
    # the one it was built against.
    bt = read(T.path_of('base.html'))
    for mark, who in (('B-1, 5 Oct 2026', 'B-1'), ('B-2, 6 Oct 2026', 'B-2')):
        if mark not in bt:
            raise SystemExit('B-2b: %s has not been applied - this round is '
                             'the tail of the tier %s took the head of'
                             % (who, who))

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
        c = cuts_for(T.code_only(raw), name)
        if c:
            plan[name] = (p, raw, c)

    total = sum(len(v[2]) for v in plan.values())

    if total == 0:
        done = sum(1 for p in T.templates() if MARK in read(p))
        print('B-2b cuts  : 0')
        print('B-2b pages : %d already carry the note' % done)
        print('B-2b applied' if check else 'B-2b ok')
        return 0

    if total != EXPECT_CUTS or len(plan) != EXPECT_PAGES:
        raise SystemExit('B-2b: measured %d cut(s) on %d page(s), the map '
                         'says %d on %d - the tree has changed since it '
                         'was measured and looked at'
                         % (total, len(plan), EXPECT_CUTS, EXPECT_PAGES))

    for name, (p, raw, c) in sorted(plan.items()):
        spans = sorted(set((a, b) for a, b, _l, _pr, _t, _s in c),
                       reverse=True)
        if len(spans) != len(c):
            raise SystemExit('B-2b: %s produced %d cut(s) over %d distinct '
                             'span(s)' % (name, len(c), len(spans)))
        last = None
        for a, b in spans:
            if last is not None and b > last:
                raise SystemExit('B-2b: overlapping cuts on %s at %d-%d'
                                 % (name, a, b))
            last = a

        text = raw
        for a, b, lit, prop, tok, sel in sorted(c, reverse=True):
            if text[a:b] != lit:
                raise SystemExit('B-2b: %s at %d reads %r, not %r'
                                 % (name, a, text[a:b], lit))
            text = text[:a] + 'var(%s)' % tok + text[b:]

        again = cuts_for(T.code_only(text), name)
        if again:
            raise SystemExit('B-2b: %s still holds %d tail literal(s) '
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
            raise SystemExit('B-2b: the note on %s did not land in a style '
                             'block - it is live CSS at %d' % (name, at))

        if not check:
            backup(p)
            write(p, text)

    print('B-2b pairs proved against base : %d, over %d token(s)'
          % (len(MAP), ntok))
    print('B-2b cuts                      : %d' % total)
    print('B-2b pages                     : %d' % len(plan))
    print('B-2b largest move              : %.1f of %.1f allowed'
          % (max(w for _t, w in MAP.values()), CEILING))
    if check:
        print('B-2b NOT APPLIED')
        return 1
    print('B-2b ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
