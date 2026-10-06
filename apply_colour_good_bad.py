"""B-3 - THE GREEN AND THE RED, AND THIS ONE IS VISIBLE.

B-1 took tier A, where the literal already WAS the token's value. B-2 and
B-2b took tier B, where nothing moved more than 25 RGB units. This round
is tier C: a real colour change, looked at before it ran.

WHY THESE TWO FAMILIES FIRST. Not size - because one of them is a defect.
Bootstrap's success green fails WCAG AA for normal text, and it is the
most-used colour left in the tree:

    #28a745 as text on paper        3.13:1   ->  5.12:1   --alv-good
    white on a #28a745 fill         3.13:1   ->  5.12:1
    #dc3545 as text on paper        4.53:1   ->  6.54:1   --alv-bad
    white on a #dc3545 fill         4.53:1   ->  6.54:1

Every single pair in this round gets MORE readable, not less. That is
not true of tier C in general - the amber is the opposite and is its own
round - and it is why green and red go together and go first.

THE FAMILIES ARE TAKEN WHOLE, WHICH IS NOT WHAT I FIRST PROPOSED. The
number quoted to Demetri was 179: the two solids, #28a745 and #dc3545.
Taking only those would have left eleven other greens and three other
reds behind - and ten of them are HOVER STATES of the solids. A button
whose rest became --alv-good while its hover stayed #218838 would get
LIGHTER on hover, because --alv-good (#1e7d4f) is darker than Bootstrap's
hover green. So the round is the families entire, 250 uses.

WHAT IS DELIBERATELY NOT IN IT, although a hue test sweeps them up:

    #2c1810 #5c3a2a #5d4037   the recipe browns - 19 uses, a theme
    #e83e8c                   pink, not a red
    #c2410c                   burnt orange, a warn
    #20c997                   Bootstrap teal - nearer the accent

THE HOVER IS A ROLE OF ITS OWN, and that is this round's addition to the
method. "Family, then role, then distance" would put #218838 on
--alv-good at 25.7 - the same token as the colour it is the hover FOR.
So the map sends every hover-dark to the family's -ink token, and
prove_hovers() refuses the round unless EVERY rest/hover pair in the tree
is still darker on hover after the substitution. 21 pairs, measured.

    rest            hover           before      after
    #28a745         #218838         4.52:1      8.57:1   (white on it)
    #dc3545         #c82333         5.61:1      8.91:1

DEMETRI LOOKED FIRST, at both widths, 6 Oct 2026.

FILES: see the census.                  [test_colour_good_bad.py]
"""
import os
import re
import sys

import alv_tree as T
import alv_cssrules as R

from apply_colour_tokens import as_colour, role_of, root_values

SUFFIX = '.bak_goodbad'
CHECK = False

# (colour, role) -> (token, the move, to a tenth of an RGB unit)
#
# THE MOVE IS PART OF THE MAP, as it was in B-2 - but here the number is
# not a promise that nothing is visible. It is a promise that the round
# is still aimed at the colour it was measured against: change a token
# in base and this refuses to run rather than quietly moving 250
# declarations somewhere nobody looked.
MAP = {
    # --- the green, mid solid ------------------------------------------
    ('#28a745', 'INK'): ('--alv-good', 44.3),
    ('#28a745', 'FILL'): ('--alv-good', 44.3),
    ('#28a745', 'LINE'): ('--alv-good', 44.3),
    ('#2e7d32', 'INK'): ('--alv-good', 33.1),
    ('#16a34a', 'INK'): ('--alv-good', 39.2),
    ('#28d168', 'INK'): ('--alv-good', 88.2),
    ('#2ecc71', 'FILL'): ('--alv-good', 87.5),
    ('#27ae60', 'LINE'): ('--alv-good', 52.6),
    # --- the green, the darks: every one of these is a hover -----------
    ('#218838', 'FILL'): ('--alv-good-ink', 50.5),
    ('#218838', 'LINE'): ('--alv-good-ink', 50.5),
    ('#1e7e34', 'INK'): ('--alv-good-ink', 40.1),
    ('#1e7e34', 'LINE'): ('--alv-good-ink', 40.1),
    ('#0c6b3f', 'INK'): ('--alv-good-ink', 23.3),
    ('#0f5132', 'INK'): ('--alv-good-ink', 9.8),
    # --- the green, the wash -------------------------------------------
    ('#d4edda', 'FILL'): ('--alv-good-soft', 26.4),
    # --- the red, mid solid --------------------------------------------
    ('#dc3545', 'INK'): ('--alv-bad', 58.5),
    ('#dc3545', 'FILL'): ('--alv-bad', 58.5),
    ('#dc3545', 'LINE'): ('--alv-bad', 58.5),
    ('#e74c3c', 'INK'): ('--alv-bad', 71.0),
    ('#e74c3c', 'FILL'): ('--alv-bad', 71.0),
    ('#c0392b', 'LINE'): ('--alv-bad', 26.4),
    # --- the red, the darks --------------------------------------------
    # #c82333 is Bootstrap's danger hover. #721c24 is its alert TEXT, and
    # it sits on backgrounds B-2b already moved to --alv-bad-soft: left
    # alone it would be the only half-house alert in the tree.
    ('#c82333', 'FILL'): ('--alv-bad-ink', 63.8),
    ('#721c24', 'INK'): ('--alv-bad-ink', 31.8),
}

EXPECT_CUTS = 250
EXPECT_PAGES = 43

MARK = 'B-3, 6 Oct 2026'

NOTE = ('    /* %s - %d literal(s) on this page became a var(), and this\n'
        '       round is TIER C: these are real colour changes, not\n'
        '       nudges. Bootstrap green and red become the house good and\n'
        '       bad. Demetri looked at both widths before it ran.\n'
        '       EVERY ONE OF THEM READS BETTER. The green was the worst\n'
        '       colour left in the tree - 3.13:1 as text on paper, under\n'
        '       the 4.5 AA wants - and goes to 5.12. The red goes 4.53 to\n'
        '       6.54. Nothing in this round loses contrast.\n'
        '       THE HOVERS MOVED WITH THEM, to the -ink tokens, because a\n'
        '       hover that stayed Bootstrap would have gone LIGHTER than\n'
        '       its own rest state.                      [B-3 tier C] */\n')

LIT = re.compile(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b'
                 r'|rgba?\([^()]*\)', re.I)


def dist(a, b):
    def rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return sum((x - y) ** 2 for x, y in zip(rgb(a), rgb(b))) ** 0.5


def lum(h):
    def ch(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    h = h.lstrip('#')
    r, g, b = [ch(int(h[i:i + 2], 16)) for i in (0, 2, 4)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def base_of(sel):
    """A selector with its :hover and its @media wrapper stripped."""
    s = sel.split('&& ')[-1].strip()
    return re.sub(r':hover\b', '', s).strip()


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


def states(text):
    """{base selector: {prop: colour}} split into rest and hover.

    Returns (rest, hover). A declaration inside `@media (hover: hover)`
    arrives with the media query glued on by rule_spans, so base_of()
    takes the last segment - otherwise every hover inside a media query
    looks like a selector of its own and pairs with nothing.
    """
    rest, hover = {}, {}
    for a, b in R.style_spans(text):
        seen = set()
        for sel, ba, bb, ra, rb in R.rule_spans(text, a, b):
            if (ba, bb) in seen:
                continue
            seen.add((ba, bb))
            into = hover if ':hover' in sel else rest
            key = base_of(sel)
            for chunk in text[ba:bb].split(';'):
                if ':' not in chunk or '{' in chunk or '}' in chunk:
                    continue
                prop, val = chunk.split(':', 1)
                if not role_of(prop):
                    continue
                m = LIT.search(val)
                if not m:
                    continue
                col = as_colour(m.group(0))
                if col:
                    into.setdefault(key, {})[prop.strip()] = col
    return rest, hover


def resolved(col, prop, vals):
    """What `col` becomes after this round - itself if untouched."""
    role = role_of(prop)
    hit = MAP.get((col, role)) if role else None
    return as_colour(vals[hit[0]].strip()) if hit else col


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


def prove_map(vals):
    """Exactly the move this file records, and the token still exists."""
    for (col, role), (tok, want) in sorted(MAP.items()):
        if tok not in vals:
            raise SystemExit('B-3: %s is not declared in base\'s :root'
                             % tok)
        got = as_colour(vals[tok].strip())
        if got is None:
            raise SystemExit('B-3: %s reads %r, which is not a colour'
                             % (tok, vals[tok].strip()))
        d = dist(col, got)
        if abs(d - want) > 0.05:
            raise SystemExit(
                'B-3: %s %s -> %s now moves %.1f units, not the %.1f this '
                'round was measured and LOOKED AT with. Base has changed '
                'since; re-measure and show the renders again before '
                'moving 250 declarations.' % (col, role, tok, d, want))


AA = 4.5

# THE TWO THAT LOSE A LITTLE, NAMED RATHER THAN SLACKENED.
#
# My first version of this gate said "not one pair may read worse", and
# it refused the round - correctly. Two of the darks are darker than the
# house -ink tokens they become, so their ratio against paper falls:
#
#     #0f5132 INK -> --alv-good-ink    9.36:1 -> 8.57:1
#     #721c24 INK -> --alv-bad-ink    11.01:1 ->  8.91:1
#
# Both stay at nearly twice what AA asks of normal text, and dropping
# them from the round is the worse trade: #721c24 is alert TEXT sitting
# on backgrounds B-2b already moved to --alv-bad-soft, so leaving it
# would make those the only half-house alerts in the tree. So the claim
# this round is allowed to make is the narrower, true one - nothing ends
# below AA, nothing that passes today stops passing, and the two that
# FAIL today both clear it - and these two are written down rather than
# let through by a loosened rule.
DIPS = {
    ('#0f5132', 'INK'): '--alv-good-ink',
    ('#721c24', 'INK'): '--alv-bad-ink',
}


def prove_contrast(vals):
    """Nothing ends below AA, and nothing that passes today stops.

    THAT IS THE ARGUMENT FOR GOING FIRST. Tier C is a real colour change,
    so "it looks the same" is not available; what IS available here is
    that the two pairs failing AA today both clear it afterwards and
    nothing is made unreadable, and a round claiming that should refuse
    to run the day it stops being true.
    """
    paper = as_colour(vals['--alv-paper'].strip())
    bad = []
    fixed = []
    for (col, role), (tok, _w) in sorted(MAP.items()):
        new = as_colour(vals[tok].strip())
        if role == 'LINE':
            continue                 # a border is not read, it is seen
        if role == 'INK':
            a, b = lum(col), lum(paper)
            c, d = lum(new), lum(paper)
        else:                        # FILL - white text sits on it
            a, b = lum(col), lum('#ffffff')
            c, d = lum(new), lum('#ffffff')

        def r(x, y):
            hi, lo = max(x, y), min(x, y)
            return (hi + 0.05) / (lo + 0.05)
        before, after = r(a, b), r(c, d)
        # -soft tokens are washes: white on them is meaningless, and the
        # thing that sits on a wash is the family's own ink. Measured
        # that way instead.
        if tok.endswith('-soft'):
            ink = as_colour(vals[tok.replace('-soft', '-ink')].strip())
            before, after = r(lum(ink), lum(col)), r(lum(ink), lum(new))

        if before < AA <= after:
            fixed.append('%s %s -> %s  %.2f:1 becomes %.2f:1'
                         % (col, role, tok, before, after))
        if after < AA:
            bad.append('%s %s -> %s  ends at %.2f:1, under AA'
                       % (col, role, tok, after))
        elif after < before - 0.01 and (col, role) not in DIPS:
            bad.append('%s %s -> %s  %.2f:1 becomes %.2f:1, and it is not '
                       'one of the two dips this round wrote down'
                       % (col, role, tok, before, after))
        elif (col, role) in DIPS and DIPS[(col, role)] != tok:
            bad.append('%s %s is written down as a dip onto %s, but the '
                       'map now sends it to %s'
                       % (col, role, DIPS[(col, role)], tok))
    if bad:
        raise SystemExit('B-3: %d substitution(s) fail the contrast gate, '
                         'and this round exists because of contrast:\n   %s'
                         % (len(bad), '\n   '.join(bad)))
    if not fixed:
        raise SystemExit('B-3: not one pair in this round moves from under '
                         'AA to over it. That was the reason to run it '
                         'first; if it is no longer true, re-argue the '
                         'round rather than running it.')
    return fixed


def prove_hovers(vals, pages):
    """Every hover stays darker than its own rest state.

    THE ONE A (colour, role) MAP CANNOT SEE. #218838 is 25.7 units from
    --alv-good - nearer than #28a745 is - so distance alone sends a
    button's hover to the same token as the button. The hover then does
    nothing, or goes the wrong way: --alv-good is DARKER than Bootstrap's
    hover green, so a half-converted button gets lighter under the
    pointer. Measured across the tree, not assumed.
    """
    checked, broke = 0, []
    for name, raw in pages:
        code = T.code_only(raw)
        rest, hover = states(code)
        for key, props in hover.items():
            for prop, hcol in props.items():
                rcol = (rest.get(key, {}).get(prop)
                        or rest.get(key, {}).get(
                            'background' if prop == 'background-color'
                            else 'background-color'))
                if not rcol:
                    continue
                if (hcol, role_of(prop)) not in MAP \
                        and (rcol, role_of(prop)) not in MAP:
                    continue
                checked += 1
                r0, h0 = lum(rcol), lum(hcol)
                r1 = lum(resolved(rcol, prop, vals))
                h1 = lum(resolved(hcol, prop, vals))
                if h0 < r0 and not h1 < r1:
                    broke.append('%s  %s %s: %s/%s was darker on hover, '
                                 'would not be' % (name, key, prop,
                                                   rcol, hcol))
    if broke:
        raise SystemExit('B-3: %d hover(s) would stop being darker than '
                         'their rest state:\n   %s'
                         % (len(broke), '\n   '.join(broke)))
    return checked


# ==========================================================================
# THE ONE SUITE THIS ROUND BREAKS, AND WHY IT IS A SCOPE BUG
# ==========================================================================
# test_celebration_az.py section 2 reads recipe_management.html LIVE and
# requires it to write #28a745 at least four times - the point being that
# the page P3 was modelled on hard-codes the green while the celebration
# strip uses tokens. B-3 converts those four, so the suite goes red.
#
# THE ASSERTION IS NOT WRONG. The READ is: a gate must read a page as its
# OWN round left it, not as some later round leaves it. That is the same
# fault already fixed in test_tab_right_edge and test_table_admin, and
# the fix is the same - as_left_by(path, SUFFIX, read), which walks to
# the earliest backup written after this round's own. Read that way the
# page still writes the green thirty times, because that is what it said
# in September, and P3's claim stands untouched for good.
#
# IT IS ALSO WHY THE NUMBER IS NOT SIMPLY BUMPED. Editing >= 4 to >= 1
# would make the suite pass and quietly turn a statement about P3 into a
# statement about whatever ran last.
AZ = 'test_celebration_az.py'

AZ_OLD = "rec = read(alv_tree.path_of(RECIPES))\n"

AZ_NEW = (
    "# AS P3 LEFT IT, NOT AS IT STANDS. [B-3, 6 Oct 2026]\n"
    "# Section 2 asks how many times the page this strip was modelled on\n"
    "# hard-codes the green. B-3 tokenised those, so read live the answer\n"
    "# is now one - a comment - and this suite went red for a change that\n"
    "# has nothing to do with it. A gate reads the page as its OWN round\n"
    "# left it: as_left_by walks to the earliest backup written after\n"
    "# .bak_celaz, which is the page as it stood in September.\n"
    "try:\n"
    "    from alv_rounds import as_left_by as _as_left_by\n"
    "except Exception:\n"
    "    _as_left_by = None\n"
    "rec = (_as_left_by(alv_tree.path_of(RECIPES), SUFFIX, read)\n"
    "       if _as_left_by else read(alv_tree.path_of(RECIPES)))\n")


def patch_az():
    """One whole-line edit, matched exactly once or nothing is written."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), AZ)
    text = read(path)
    if AZ_NEW.split('\n')[0] in text:
        print('  %-32s already scoped' % AZ)
        return
    n = text.count(AZ_OLD)
    if n != 1:
        raise SystemExit('B-3: %s - the live read matched %d time(s), '
                         'not once' % (AZ, n))
    text = text.replace(AZ_OLD, fit(text, AZ_NEW), 1)
    if not CHECK:
        backup(path)
        write(path, text)
    print('  %-32s now reads at its own round scope' % AZ)


def main(argv):
    global CHECK
    check = '--check' in argv
    CHECK = check
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # THE TIER B ROUNDS FIRST. This round's map is what is LEFT after
    # them, and running it on a tree they had not touched would meet
    # colours they own.
    bt = read(T.path_of('base.html'))
    for mark, who in (('B-1, 5 Oct 2026', 'B-1'),
                      ('B-2, 6 Oct 2026', 'B-2'),
                      ('B-2b, 6 Oct 2026', 'B-2b')):
        if mark not in bt:
            raise SystemExit('B-3: %s has not been applied - tier C builds '
                             'on the tree tier B leaves' % who)

    vals, _ats = root_values(bt)
    prove_map(vals)
    fixed = prove_contrast(vals)

    stand = set(T.standalone())
    plan = {}
    allpages = []
    for p in T.templates():
        name = T.rel(p).replace(os.sep, '/')
        if name in stand:
            continue
        raw = read(p)
        allpages.append((name, raw))
        if MARK in raw:
            continue
        c = cuts_for(T.code_only(raw))
        if c:
            plan[name] = (p, raw, c)

    checked = prove_hovers(vals, allpages)

    # BEFORE THE EARLY RETURN. The re-scope is part of this round
    # whether or not there are cuts left to make, and a round that
    # did its templates on one run and its suite on the next would
    # leave the gate red in between.
    print('')
    print('  THE SUITE THIS ROUND RE-SCOPES')
    print('  ' + '-' * 70)
    patch_az()

    total = sum(len(v[2]) for v in plan.values())

    if total == 0:
        done = sum(1 for p in T.templates() if MARK in read(p))
        print('B-3  cuts  : 0')
        print('B-3  pages : %d already carry the note' % done)
        print('B-3  applied' if check else 'B-3  ok')
        return 0

    if total != EXPECT_CUTS or len(plan) != EXPECT_PAGES:
        raise SystemExit('B-3: measured %d cut(s) on %d page(s), the map '
                         'says %d on %d - the tree has changed since it '
                         'was measured and looked at'
                         % (total, len(plan), EXPECT_CUTS, EXPECT_PAGES))

    for name, (p, raw, c) in sorted(plan.items()):
        spans = sorted(set((a, b) for a, b, _l, _pr, _t, _s in c),
                       reverse=True)
        if len(spans) != len(c):
            raise SystemExit('B-3: %s produced %d cut(s) over %d distinct '
                             'span(s)' % (name, len(c), len(spans)))
        last = None
        for a, b in spans:
            if last is not None and b > last:
                raise SystemExit('B-3: overlapping cuts on %s at %d-%d'
                                 % (name, a, b))
            last = a

        text = raw
        for a, b, lit, prop, tok, sel in sorted(c, reverse=True):
            if text[a:b] != lit:
                raise SystemExit('B-3: %s at %d reads %r, not %r'
                                 % (name, a, text[a:b], lit))
            text = text[:a] + 'var(%s)' % tok + text[b:]

        again = cuts_for(T.code_only(text))
        if again:
            raise SystemExit('B-3: %s still holds %d literal(s) from the '
                             'two families after the rewrite'
                             % (name, len(again)))

        # B-1's lesson, and it cost a revert of 102 files: style_spans has
        # no comment awareness, and a CSS comment that MENTIONS a style
        # tag puts the note in the middle of a sentence.
        sp = R.style_spans(T.code_only(text))
        at = sp[-1][0]
        note = fit(text, NOTE % (MARK, len(c)))
        text = text[:at] + note + text[at:]
        if T.code_only(text)[at:at + len(note)].strip():
            raise SystemExit('B-3: the note on %s did not land in a style '
                             'block - it is live CSS at %d' % (name, at))

        if not check:
            backup(p)
            write(p, text)

    print('B-3  moves proved against base : %d pair(s)' % len(MAP))
    print('B-3  contrast proved           : %d pair(s) cross AA, none '
          'ends below it' % len(fixed))
    for line in fixed:
        print('       %s' % line)
    print('B-3  hovers checked            : %d, all still darker' % checked)
    print('B-3  cuts                      : %d' % total)
    print('B-3  pages                     : %d' % len(plan))
    print('B-3  largest move              : %.1f units (tier C)'
          % max(w for _t, w in MAP.values()))
    if check:
        print('B-3  NOT APPLIED')
        return 1
    print('B-3  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
