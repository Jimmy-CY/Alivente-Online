"""B-1 - 957 LITERALS THAT ARE ALREADY THE TOKEN'S VALUE.

   Section B's map, agreed 5 Oct 2026, sorts every hard-coded colour in
   the tree into three tiers. This round is tier A and nothing else:

       A   the literal IS the token's value      957 uses, 102 pages
       B   a nudge, 25 RGB units or less       1,101 uses,  95 pages
       C   a real colour change                  557 uses,  74 pages

   THIRTEEN SUBSTITUTIONS COVER ALL 957. `color: white` becomes
   `color: var(--alv-on-accent)`, `background: #f8f9fa` becomes
   `background: var(--alv-surface)`, and so on. Every one resolves to the
   byte-identical computed value, because the gate below refuses to run
   unless base's :root says so.

   THE PROOF IS IN THE VALUE, NOT THE PICTURE. main() reads base.html,
   pulls the :root value of all thirteen tokens, normalises it and
   refuses the whole round unless each equals the literal it is replacing
   character for character. A render cannot prove this - the two pictures
   are the same picture - so the render in the suite is smoke, and this
   is the gate.

   ROLE DECIDES THE TOKEN, which is why this cannot be a string replace.
   White is --alv-on-accent as ink and --alv-paper as a fill: the same
   six characters, two different meanings, and base happens to give both
   the same value today. A blind replace would collapse that distinction
   and the next time the house changes one of them it would take the
   other with it.

   THE TWELVE STANDALONE TEMPLATES ARE EXEMPT AND MUST STAY THAT WAY. A
   template with no {% extends %} never sees base, so :root is not in
   the document and var(--alv-surface) resolves to NOTHING - and
   xhtml2pdf, which renders four of them, does not support var() at all.
   CS-2 already reads that set off the markup. 169 uses live there and
   keep their literals; the suite asserts that every non-browser render
   path in the tree lands inside the set.

   AND A BODY IS WALKED ONCE. rule_spans reports `.a, .b { ... }` under
   BOTH selector names with the SAME body span. DR-2b cut one of those
   twice and destroyed 14 rules in title_deeds_management while every
   count still passed. The cut list here is a set, overlaps are refused,
   and the census that produced 957 had to be corrected for the same
   thing - it read 981 until the bodies were deduped.

   FILES: 102 templates.                       [test_colour_tokens.py]
"""
import os
import re
import sys

import alv_tree as T
import alv_cssrules as R

SUFFIX = '.bak_coltok'

# (colour, role) -> token. TIER A ONLY. Role is the property's job:
#   INK   color
#   FILL  background, background-color
#   LINE  border*, outline*
MAP = {
    ('#ffffff', 'INK'): '--alv-on-accent',
    ('#ffffff', 'FILL'): '--alv-paper',
    ('#ffffff', 'LINE'): '--alv-paper',
    ('#f8f9fa', 'FILL'): '--alv-surface',
    ('#0e7c8b', 'INK'): '--alv-accent',
    ('#0e7c8b', 'FILL'): '--alv-accent',
    ('#0e7c8b', 'LINE'): '--alv-accent',
    ('#e9ecef', 'LINE'): '--alv-surface-deep',
    ('#f1f3f5', 'FILL'): '--alv-line-soft',
    ('#f2cecb', 'LINE'): '--alv-bad-line',
    ('#bfe0cd', 'LINE'): '--alv-good-line',
    ('#0a5e6a', 'FILL'): '--alv-accent-ink',
    ('#e6f4ec', 'FILL'): '--alv-good-soft',
}

EXPECT_CUTS = 957
EXPECT_PAGES = 102

MARK = 'B-1, 5 Oct 2026'

NOTE = ('    /* %s - %d literal(s) on this page became a var().\n'
        '       Each one was already the byte-identical value of the\n'
        '       token that replaced it, read from base\'s :root, so\n'
        '       nothing here moved. What changes is that the page is on\n'
        '       the token and will follow when the house does.\n'
        '       Tier A of the Section B map; B and C move a pixel and\n'
        '       are separate rounds.                   [B-1 tier A] */\n')

# Every way one of those colours can be written in a declaration value.
LIT = re.compile(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b'
                 r'|rgba?\([^()]*\)'
                 r'|(?<![-\w])white(?![-\w])', re.I)

KEYWORD = {'white': '#ffffff'}


def as_colour(lit):
    """The opaque colour this literal names, or None.

    THE KEYWORDS MATTER, and that is DR-2a's lesson restated: its first
    build did not know `white` is #ffffff and filed four declarations
    under "really differs". Here 455 of the 957 are spelled `white` and
    32 more `#fff` - two thirds of the round is written in a form a hex
    match alone would miss entirely.

    Translucent rgba() returns None. A var() cannot be dropped into an
    rgba() channel triple, and a shade is not a colour.
    """
    s = lit.strip().lower()
    if s in KEYWORD:
        return KEYWORD[s]
    if s.startswith('#'):
        h = s[1:]
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        return '#' + h
    m = re.match(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*'
                 r'(?:,\s*([0-9.]+)\s*)?\)$', s)
    if not m:
        return None
    if m.group(4) is not None and float(m.group(4)) < 0.999:
        return None
    return '#%02x%02x%02x' % tuple(int(m.group(i)) for i in (1, 2, 3))


def role_of(prop):
    """The property's JOB, not its name."""
    p = prop.strip().lower()
    if p == 'color':
        return 'INK'
    if p in ('background', 'background-color'):
        return 'FILL'
    if p.startswith(('border', 'outline')):
        # A width, a radius or a style is not a colour, and -offset and
        # -collapse are not either.
        if p.endswith(('-radius', '-width', '-style', '-collapse',
                       '-spacing', '-offset')):
            return None
        return 'LINE'
    return None


def cuts_for(text):
    """[(start, end, literal, prop, token, selector), ...], by offset.

    Read against code_only(text), whose comments are blanked IN PLACE,
    line for line - so these offsets are the offsets in the raw file and
    nothing inside a comment can be found.
    """
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
                    tok = MAP.get((col, role))
                    if tok:
                        out.append((voff + m.start(), voff + m.end(),
                                    m.group(0), prop.strip(), tok, sel))
    return sorted(out)


def root_values(base_text):
    """Every --alv- name declared in a :root of base, and where they are.

    BASE HAS TWO :root BLOCKS, in two different <style> elements - six
    accent tokens at one offset and the other 74 at another, a leftover
    of CS-1 moving blocks out of the head. A reader that takes the first
    one finds six tokens and concludes --alv-good-line does not exist,
    which is what the first build of this round concluded.

    So every :root is read, in document order, and last wins - which is
    what a browser does with two declarations of equal specificity. The
    two blocks happen to share no name today, and a name declared twice
    with two different values is refused rather than resolved, because
    at that point which value a page gets depends on which block the
    reader looked at.
    """
    code = T.code_only(base_text)
    out = {}
    ats = []
    for m in re.finditer(r':root\s*\{', code):
        depth, i = 1, m.end()
        while i < len(code) and depth:
            if code[i] == '{':
                depth += 1
            elif code[i] == '}':
                depth -= 1
            i += 1
        ats.append(m.start())
        for k, v in re.findall(r'(--alv-[a-z0-9-]+)\s*:\s*([^;]+);',
                               code[m.end():i - 1]):
            if k in out and out[k].strip() != v.strip():
                raise SystemExit('B-1: base declares %s twice, as %r and '
                                 '%r - which one a page reads depends on '
                                 'the cascade and this round will not '
                                 'guess' % (k, out[k].strip(), v.strip()))
            out[k] = v
    if not ats:
        raise SystemExit('B-1: base.html has no :root - there are no '
                         'tokens to point at')
    return out, ats


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


def prove_map():
    """THE WHOLE ROUND RESTS ON THIS. Refuse unless base agrees."""
    bp = T.path_of('base.html')
    text = read(bp)
    vals, ats = root_values(text)

    code = T.code_only(text)
    hl = code.lower()
    for at in ats:
        if not (hl.index('<head') < at < hl.index('</head>')):
            raise SystemExit('B-1: a :root of base at %d is not in <head> '
                             '- a page whose own style block is parsed '
                             'first would read a token that is not there '
                             'yet' % at)
        before = code[:at]
        if len(re.findall(r'\{%\s*block\b', before)) > \
           len(re.findall(r'\{%\s*endblock\b', before)):
            raise SystemExit('B-1: a :root of base at %d is inside a '
                             '{%% block %%}, so a child template could '
                             'replace it and every var() in this round '
                             'would resolve to nothing' % at)

    for (col, role), tok in sorted(MAP.items()):
        if tok not in vals:
            raise SystemExit('B-1: %s is not declared in base\'s :root'
                             % tok)
        got = as_colour(vals[tok].strip())
        if got != col:
            raise SystemExit('B-1: %s is %r in base, not %s - this round '
                             'claims the substitution cannot move a pixel '
                             'and that claim is false'
                             % (tok, vals[tok].strip(), col))
    return len(vals)


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    ntok = prove_map()

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
        print('B-1  cuts  : 0')
        print('B-1  pages : %d already carry the note' % done)
        print('B-1  applied' if check else 'B-1  ok')
        return 0

    # EXACT COUNTS, AND IT REFUSES RATHER THAN DOING HALF.
    if total != EXPECT_CUTS or len(plan) != EXPECT_PAGES:
        raise SystemExit('B-1: measured %d cut(s) on %d page(s), the map '
                         'says %d on %d - the tree has changed since it '
                         'was measured and the map needs re-reading '
                         'before anything is rewritten'
                         % (total, len(plan), EXPECT_CUTS, EXPECT_PAGES))

    for name, (p, raw, c) in sorted(plan.items()):
        # A SET, AND OVERLAPS REFUSED. DR-2b produced two identical cuts
        # from one grouped rule and applied both.
        spans = sorted(set((a, b) for a, b, _l, _pr, _t, _s in c),
                       reverse=True)
        if len(spans) != len(c):
            raise SystemExit('B-1: %s produced %d cut(s) over %d distinct '
                             'span(s)' % (name, len(c), len(spans)))
        last = None
        for a, b in spans:
            if last is not None and b > last:
                raise SystemExit('B-1: overlapping cuts on %s at %d-%d'
                                 % (name, a, b))
            last = a

        text = raw
        for a, b, lit, prop, tok, sel in sorted(c, reverse=True):
            if text[a:b] != lit:
                raise SystemExit('B-1: %s at %d reads %r, not %r'
                                 % (name, a, text[a:b], lit))
            text = text[:a] + 'var(%s)' % tok + text[b:]

        # NOTHING LEFT BEHIND, checked on the rewritten text.
        again = cuts_for(T.code_only(text))
        if again:
            raise SystemExit('B-1: %s still holds %d tier-A literal(s) '
                             'after the rewrite' % (name, len(again)))

        # THE NOTE GOES IN A REAL STYLE BLOCK, and that needs the
        # BLANKED text to find one. style_spans has no comment
        # awareness, and lease_renewal_report.html carries a CSS comment
        # that MENTIONS `<style>` - "re-ordering the <style> blocks
        # cannot grey it". Read raw, style_spans believed that prose was
        # a style element and the note was written into the middle of
        # the sentence, splitting the word `blocks`. Nothing measurable
        # changed: no declaration, no rule, no computed value, so every
        # count in the suite still passed and the page's own render test
        # four modules away was the only thing that noticed.
        #
        # CO-1 wrote the same lesson the other way round - `/*` is not a
        # comment opener in markup. A tag inside a comment is not a tag.
        sp = R.style_spans(T.code_only(text))
        at = sp[-1][0]
        note = fit(text, NOTE % (MARK, len(c)))
        text = text[:at] + note + text[at:]
        # AND IT MUST BE A COMMENT WHERE IT LANDED. If the insert point
        # were inside an existing comment the `/*` would nest, the outer
        # `*/` would close early, and what followed would become live
        # CSS. Blanked, a comment is spaces; anything else is not.
        if T.code_only(text)[at:at + len(note)].strip():
            raise SystemExit('B-1: the note on %s did not land in a '
                             'style block - it is live CSS at %d'
                             % (name, at))

        if not check:
            backup(p)
            write(p, text)

    print('B-1  tokens proved against base : %d of %d' % (len(MAP), ntok))
    print('B-1  cuts                       : %d' % total)
    print('B-1  pages                      : %d' % len(plan))
    print('B-1  standalone exempt          : %d' % len(stand))
    if check:
        print('B-1  NOT APPLIED')
        return 1
    print('B-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
