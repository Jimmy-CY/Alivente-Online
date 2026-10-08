# -*- coding: utf-8 -*-
"""B-5a - the neutrals, tiers A and B, at the scope decision 9 set.

Decision 2: "Convert the greys to the house ink ramp; leave #000000
alone until I survey it." The survey is S-a and it is done, so the black
half is settled and this round is the greys.

=====================================================================
THE SHAPE OF THIS ROUND IS ITSELF THE ARGUMENT FOR DECISION 9
=====================================================================

    inline style= attributes   109
    inside <script>             72
    page stylesheets            11

B-1, B-2 and B-2b already converted the greys in stylesheets - that is
why only eleven are left there. NINETY-TWO PER CENT OF WHAT REMAINS IS
IN MARKUP AND JAVASCRIPT, which Section B could not see at all until
CR-1 taught alv_cssrules to read outside a <style> block.

=====================================================================
THE TIERS, AND WHY THIS ROUND HAS A SAFE HALF WHERE B-4 HAD NONE
=====================================================================

    A   44  the literal IS the token's value
    B  128  within 25 units, invisible
    C  100  a real colour change              - LEFT FOR B-5b

ROLE PICKS THE TOKEN FAMILY; DISTANCE ONLY BREAKS TIES INSIDE IT. The
first version of this map chose purely by distance and got twelve of
170 semantically wrong: `color: #dee2e6` became var(--alv-line) and
`color: #fff` became var(--alv-paper). Both are the right COLOUR and
the wrong NAME, and the name is the meaning - somebody later retuning
--alv-line would be moving text rather than a hairline.

AND THE SAME LITERAL CAN SIT IN TWO TIERS AT ONCE. #6c757d as ink is
16.8 units from --alv-neutral, tier B and invisible; as a border the
nearest line token is far enough to be tier C. Distance alone cannot
see that, which is the whole argument for family, then role, then
distance.

B-4 had 6 safe of 62 and no half worth landing. This has 192 of 275,
and the line is drawn by distance rather than by anybody's judgement.

=====================================================================
WHAT IS LEFT ALONE
=====================================================================

    #000, 19 uses   S-a SETTLED THESE. 14 are inside @media print, 8 are
                    color-mix darkening functions, 5 are view_recipe's
                    FDA Nutrition Facts panel - a specified design - and
                    the two genuine drifts are handled by B-4 and B-4b.
                    Decision 2 said leave black until surveyed; it has
                    been surveyed and the answer is leave it.

    6 in <script>   CANVAS. THE FIRST TIME CR-1's TRAP ACTUALLY BITES.
                    A 2D context cannot resolve a custom property, so
                    var() there is not a colour and the chart vanishes.

    16 in <script>  js_colour_context cannot classify them. A round
                    refuses what it cannot classify.

    81 tier C       #adb5bd 37 uses at 56 units, #ced4da 20 at 33. Real
                    changes, each one a decision, and the colour map
                    says the render IS that decision. B-5b, with renders.

=====================================================================
THE GATE HOLE B-4 EXPOSED, CLOSED HERE
=====================================================================

B-4 checked that every INK conversion improved contrast. It never
checked a FILL conversion against the ink already sitting on it, so
.btn-edit:hover went from 9.77:1 to 3.90:1 - the background moved to
dark ochre and the #000 ink stayed put. One failure in 26 pairs, found
by reading the result rather than by the gate.

THIS ROUND EVALUATES THE PAIR. Every rule whose fill OR ink this round
touches has its (background, colour) contrast measured before and
after, and the round refuses if any pair drops below AA.

FILES: the pages in b5work.json (+ .bak_neutrals), alv_rounds.py, the
PS1 $suites, alv_impact.py, test_cssrules_outside.py, and the new
test_neutrals.py. No base, no token - the IMPACT SET.

=====================================================================
THE SIX NUMBERS THIS ROUND MOVES, AND IT OWNS ALL SIX
=====================================================================

CR-1's census counts colour literals outside page CSS across the whole
tree. B-5a converts 106 in style= attributes and 50 inside <script>, so
six of its numbers come down - measured, not guessed:

    MARKUP_STYLE  224 -> 118   -106, the attr cuts exactly
    SCRIPT        253 -> 203    -50, the script cuts exactly
    PAGES          47 ->  40     -7 pages lose their last literal
    style-attr     98 ->  61
    style-prop     37 ->  24     those two are the -50, split by context
    safe          135 ->  85

AND ONE NUMBER THAT MUST NOT MOVE: canvas 27 and unknown 91 are
untouched, because this round converts only what js_colour_context
calls var-safe. 203 - 85 = 118 = 27 + 91, still, which is the arithmetic
saying the refusals were honoured.

B-4's push failed the gate on exactly this - it moved four of these and
did not update them - and the sweep had not caught it because
alv_impact.COUNTERS was missing the suite. test_neutrals.py reads the
whole tree too (sections 3 and 5), so it joins COUNTERS here rather
than waiting for a later round to discover the same hole again.
"""
import collections
import json
import os
import re
import sys

SUFFIX = '.bak_neutrals'
MARK = 'B-5a, 8 Oct 2026'
SUITE_NAME = 'test_neutrals.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_cssrules as R                                   # noqa: E402
import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
WORK = os.path.join(ROOT, 'b5work.json')
CHECK = False

TOKVAL = {'--alv-paper': '#ffffff', '--alv-surface': '#f8f9fa',
          '--alv-surface-deep': '#e9ecef', '--alv-ink': '#21343c',
          '--alv-ink-soft': '#5b6b73', '--alv-ink-faint': '#8a979d',
          '--alv-ink-strong': '#41535c', '--alv-line': '#e3e8ea',
          '--alv-line-soft': '#f1f3f5', '--alv-neutral': '#616c74',
          '--alv-neutral-soft': '#eef1f2'}

# S-a settled the black. Decision 2 said leave it until surveyed.
LEAVE_LIT = {'#000': 'S-a: 14 print, 8 color-mix, 5 the FDA panel, and the '
                     'two genuine drifts go to B-4 and B-4b',
             '#000000': 'see #000'}

EXPECT_CUTS = 158
EXPECT_PAGES = 32
EXPECT_CANVAS = 5
EXPECT_UNKNOWN = 9


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
    r, g, b = c
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    if la is None or lb is None:
        return None
    hi, lo = max(la, lb), min(la, lb)
    return (hi + .05) / (lo + .05)


def resolve(v):
    """The hex a declaration's value ends up as, var() or literal."""
    if not v:
        return None
    m = re.search(r'var\((--[\w-]+)\)', v)
    if m:
        return TOKVAL.get(m.group(1))
    m = re.search(r'#[0-9a-fA-F]{3,8}(?![\w-])', v)
    return m.group(0) if m else None


def role_of(prop):
    p = prop.lower()
    if 'border' in p or p.startswith('outline'):
        return 'border'
    if 'background' in p:
        return 'fill'
    if p in ('color', 'fill', 'stroke') or p.endswith('color'):
        return 'ink'
    if 'shadow' in p:
        return 'shadow'
    return 'other'


def decls_of(code, ba, bb):
    d = {}
    for ch in code[ba:bb].split(';'):
        if ':' in ch:
            k = R.norm(ch.partition(':')[0]).lower()
            if k and not k.startswith('--'):
                d[k] = R.norm(ch.partition(':')[2])
    return d


def pair_table(code):
    """{selector: (background_hex, colour_hex)} for every rule that sets
    both - the thing B-4's gate never looked at."""
    out = {}
    for a, b in R.style_spans(code):
        bodies = collections.OrderedDict()
        for sel, ba, bb, _x, _y in R.rule_spans(code, a, b):
            bodies.setdefault((ba, bb), []).append(sel)
        for (ba, bb), sels in bodies.items():
            d = decls_of(code, ba, bb)
            bg = resolve(d.get('background') or d.get('background-color'))
            ink = resolve(d.get('color'))
            if bg and ink:
                for s in sels:
                    out[s] = (bg, ink)
    return out


def base_tokens():
    """Every --alv-* base declares on :root, name -> value.

    THE FAULT CLASS THIS CLOSES: a round that writes var(--alv-whatever)
    when base declares no such token produces an invalid declaration,
    the property falls back to whatever it inherits, and NOTHING SAYS
    SO - no parse error, no warning, just the wrong colour on a page
    nobody opened. Base carries the tokens in TWO separate :root rules
    and a map built from the first one alone is missing six, which is
    how this check came to be written.
    """
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


def census(planned):
    """CR-1's census, read over the tree AS THIS ROUND WOULD LEAVE IT.

    `planned` maps full path -> the new text. Every other template is
    read from disk. Nothing is written: the round computes the numbers
    it is about to claim, checks them, and only then writes - a patcher
    verifies, then writes, never the reverse.

    This is a copy of the loop in test_cssrules_outside.py section 6
    and it has to stay one. If that loop changes, this must follow, and
    the exact-match gate on the six numbers is what will say so.
    """
    stand = set(T.standalone())
    n_markup = n_script = n_sa = 0
    pages = set()
    ctx = collections.Counter()
    for p in T.templates():
        raw = planned.get(p) or read(p)
        t = T.code_only(raw)
        jsx = T.code_only_js(raw)
        is_sa = T.rel(p) in stand
        hit = 0
        for a, b in R.style_attr_spans(t):
            c = len(R.colour_spans(t, a, b))
            hit += c
            if is_sa:
                n_sa += c
            else:
                n_markup += c
        for a, b in R.script_spans(jsx):
            for s, _e, _l in R.colour_spans(jsx, a, b):
                hit += 1
                if not is_sa:
                    n_script += 1
                    ctx[R.js_colour_context(jsx, s, a)] += 1
        if hit and not is_sa:
            pages.add(T.rel(p))
    out = {'MARKUP_STYLE': n_markup, 'SCRIPT': n_script,
           'PAGES': len(pages), 'STANDALONE': n_sa,
           'safe': sum(ctx.get(k, 0) for k in R.VAR_SAFE)}
    for k in ('style-attr', 'style-prop', 'css-text', 'canvas', 'unknown'):
        out[k] = ctx.get(k, 0)
    return out


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('B-5a  already applied')
        return 1 if CHECK else 0
    if not os.path.isfile(WORK):
        raise SystemExit('B-5a: b5work.json is not beside the patcher. It is '
                         'the measured work list and the round will not '
                         'guess it.')
    work = json.load(open(WORK, encoding='utf-8'))

    # ---- every token this round writes must EXIST ------------------
    have = base_tokens()
    wants = sorted({r['tok'] for r in work
                    if r['tier'] in ('A', 'B') and r['lit'] not in LEAVE_LIT})
    absent = [t for t in wants if t not in have]
    if absent:
        raise SystemExit('B-5a: base declares no %s. A var() naming a token '
                         'base has not got is an invalid declaration, the '
                         'property silently falls back to what it inherits, '
                         'and nothing anywhere says so.' % ', '.join(absent))
    print('B-5a  %d token(s) written, all %d declared on base :root'
          % (len(wants), len(wants)))

    planned = {}
    cuts = collections.Counter()
    skipped = collections.Counter()

    for p in sorted(T.templates()):
        rel = T.rel(p)
        mine = [r for r in work if r['page'] == rel
                and r['tier'] in ('A', 'B')
                and r['lit'] not in LEAVE_LIT]
        if not mine:
            continue
        raw = read(p)
        code = T.code_only(raw)
        js = T.code_only_js(raw)
        # KEYED ON (literal, role), NEVER ON THE LITERAL ALONE.
        # #6c757d is tier B as ink and tier C as a border. A dict keyed
        # on the literal collapses the two and converts the border with
        # the ink token - which is the exact fault the role-first map was
        # written to remove, put straight back in by the patcher.
        want = {(r['lit'], r['role']): r['tok'] for r in mine}
        spans = {}

        # ---- 1. CSS -------------------------------------------------
        for a, b in R.style_spans(code):
            bodies = collections.OrderedDict()
            for sel, ba, bb, _x, _y in R.rule_spans(code, a, b):
                bodies.setdefault((ba, bb), []).append(sel)
            for (ba, bb), sels in bodies.items():
                for prop, val in decls_of(code, ba, bb).items():
                    for m in re.finditer(r'#[0-9a-fA-F]{3,8}(?![\w-])', val):
                        lit = m.group(0).lower()
                        tok = want.get((lit, role_of(prop)))
                        if tok is None:
                            continue
                        d = R.decl_span(code, ba, bb, prop)
                        if d is None:
                            raise SystemExit('B-5a: decl_span lost %s / %s '
                                             'on %s' % (sels[0], prop, rel))
                        cur = spans.get(d, code[d[0]:d[1]])
                        new = re.sub(re.escape(lit), 'var(%s)' % tok,
                                     cur, flags=re.I)
                        if new == cur:
                            continue
                        spans[d] = new
                        cuts['css'] += 1

        # ---- 2. inline style= attributes ---------------------------
        for a, b in R.style_attr_spans(code):
            for s, e, l in R.colour_spans(code, a, b):
                lit = l.lower()
                prop = (re.findall(r'([-\w]+)\s*:\s*[^;:]*$', code[a:s])
                        or ['color'])[-1].lower()
                tok = want.get((lit, role_of(prop)))
                if tok is None:
                    continue
                spans[(s, e)] = 'var(%s)' % tok
                cuts['attr'] += 1

        # ---- 3. <script>, var-safe only ----------------------------
        for a, b in R.script_spans(js):
            for s, e, l in R.colour_spans(js, a, b):
                lit = l.lower()
                prop = (re.findall(r'([-\w]+)\s*[:=]\s*[^;:=]*$',
                                   js[max(a, s - 80):s])
                        or ['color'])[-1].lower()
                tok = want.get((lit, role_of(prop)))
                if tok is None:
                    continue
                ctx = R.js_colour_context(js, s, a)
                if ctx not in R.VAR_SAFE:
                    skipped[ctx] += 1
                    continue
                spans[(s, e)] = 'var(%s)' % tok
                cuts['script'] += 1

        if not spans:
            continue
        ordered = sorted(spans, reverse=True)
        for i in range(1, len(ordered)):
            if ordered[i][1] > ordered[i - 1][0]:
                raise SystemExit('B-5a: overlapping edits on %s' % rel)
        out = raw
        for sp in ordered:
            out = out[:sp[0]] + spans[sp] + out[sp[1]:]
        planned[p] = out

    total = sum(cuts.values())
    print('B-5a  pages        %d' % len(planned))
    print('B-5a  css          %d' % cuts['css'])
    print('B-5a  style= attrs %d' % cuts['attr'])
    print('B-5a  script       %d  (var-safe only)' % cuts['script'])
    print('B-5a  total        %d' % total)
    print('B-5a  skipped in script: %s' % dict(skipped))

    if skipped.get('canvas', 0) != EXPECT_CANVAS:
        raise SystemExit('B-5a: %d canvas literal(s) skipped, expected %d. A '
                         'canvas cannot resolve var() and the chart would '
                         'vanish.' % (skipped.get('canvas', 0),
                                      EXPECT_CANVAS))
    if skipped.get('unknown', 0) != EXPECT_UNKNOWN:
        raise SystemExit('B-5a: %d unclassifiable literal(s), expected %d'
                         % (skipped.get('unknown', 0), EXPECT_UNKNOWN))
    if total != EXPECT_CUTS:
        raise SystemExit('B-5a: %d cuts, expected %d' % (total, EXPECT_CUTS))
    if len(planned) != EXPECT_PAGES:
        raise SystemExit('B-5a: %d pages, expected %d'
                         % (len(planned), EXPECT_PAGES))

    # ---- THE PAIR GATE - the hole B-4 exposed ----------------------
    worse = []
    pairs = 0
    for p, new in planned.items():
        was = pair_table(T.code_only(read(p)))
        now = pair_table(T.code_only(new))
        for sel, (bg, ink) in now.items():
            if sel not in was:
                continue
            a1 = contrast(*was[sel])
            a2 = contrast(bg, ink)
            if a1 is None or a2 is None:
                continue
            pairs += 1
            if a2 < 4.5 and a2 < a1 - 0.01:
                worse.append('%s %s  %.2f -> %.2f  (%s on %s)'
                             % (T.rel(p), sel, a1, a2, ink, bg))
    if worse:
        raise SystemExit('B-5a: %d fill/ink pair(s) would drop below AA: %s'
                         % (len(worse), worse[:4]))
    print('B-5a  %d fill/ink pair(s) checked, not one drops below AA' % pairs)

    # ---- the black must all survive --------------------------------
    for p, new in planned.items():
        a = T.code_only(read(p)).lower()
        b = T.code_only(new).lower()
        for lit in LEAVE_LIT:
            if a.count(lit) != b.count(lit):
                raise SystemExit('B-5a: %s lost a %s - S-a settled those'
                                 % (T.rel(p), lit))

    # ---- it must still parse ---------------------------------------
    for p, new in planned.items():
        code = T.code_only(new)
        if code.count('{') != code.count('}'):
            raise SystemExit('B-5a: %s has unbalanced braces' % T.rel(p))
        try:
            for a, b in R.style_spans(code):
                R.rule_spans(code, a, b)
        except Exception as e:
            raise SystemExit('B-5a: %s would not parse - %s' % (T.rel(p), e))

    # ---- what the census will read once this is applied -------------
    # Computed off the PLAN, before anything is written, so the round
    # refuses on a mismatch rather than leaving CR-1's suite red.
    after = census(planned)
    for name, want_n in (('MARKUP_STYLE', 118), ('SCRIPT', 203),
                         ('PAGES', 40), ('style-attr', 61),
                         ('style-prop', 24), ('safe', 85)):
        if after[name] != want_n:
            raise SystemExit('B-5a: the census would read %s = %d, not %d. '
                             'The six numbers this round owns were measured '
                             'on 8 Oct; one of them has moved since and the '
                             'round will not write a number it has not '
                             'checked.' % (name, after[name], want_n))
    # AND THE ONE THAT MUST NOT MOVE.
    if after['canvas'] != 27 or after['unknown'] != 91:
        raise SystemExit('B-5a: canvas/unknown read %d/%d, not 27/91 - this '
                         'round converts only what js_colour_context calls '
                         'var-safe, so neither may change'
                         % (after['canvas'], after['unknown']))
    print('B-5a  census after: 224->118 markup, 253->203 script, 47->40 '
          'pages, 98->61 / 37->24 ctx, 135->85 safe; canvas 27 and '
          'unknown 91 unmoved')

    # ======================================================================
    # EVERY ANCHOR IS RESOLVED BEFORE ONE BYTE IS WRITTEN.
    # ======================================================================
    # This block used to sit inside `if not CHECK:` AFTER the 32 pages had
    # been written, and on 8 Oct it did exactly what that shape makes
    # possible: B-4b appended itself to the tail of ROUNDS between B-5a
    # being built and being applied, B-5a anchor no longer matched, and
    # the round raised with the pages already on disk and the round
    # unregistered. A gate refuses rather than doing half, and half is
    # what it did.
    #
    # Now `reg` is built first - every anchor found, every replacement
    # computed, nothing written - and --check proves the registration
    # will land as well as the pages. Only then does anything move.
    reg = {}
    if True:
        # ---- 1. alv_rounds.ROUNDS ----------------------------------
        NOTE = """    # B-5a, 8 Oct 2026 - the grey neutrals. 158 literals on 32
    # pages become ink-ramp tokens: 106 in inline style= attributes,
    # 50 inside <script>, and TWO in a page stylesheet. That split is
    # the whole argument for decision 9 - B-1, B-2 and B-2b had
    # already taken the greys out of the CSS, and Section B could not
    # see the markup or the script at all until CR-1.
    #
    # ROLE PICKS THE TOKEN, DISTANCE ONLY BREAKS TIES INSIDE IT. A
    # distance-only map got twelve wrong: color:#dee2e6 -> --alv-line
    # is the right colour under a line's name, and the name is the
    # meaning. #fff as ink takes --alv-on-accent, not --alv-paper.
    #
    # AND ONE LITERAL CAN SIT IN TWO TIERS. #6c757d is 16.8 units from
    # --alv-neutral as ink and 198 from --alv-line as a border, so the
    # want table is keyed on (literal, role) - a dict keyed on the
    # literal alone collapses the two and converts the border with the
    # ink token.
    #
    # Refused: 5 canvas literals (a 2D context cannot resolve a custom
    # property and the chart would vanish) and 9 js_colour_context
    # cannot classify. Left: the black S-a settled, and 81 tier C uses
    # that are changes of appearance - B-5b, with renders.
    '%s',
""" % SUFFIX
        # THE TAIL MOVES. Every round appends itself here, so the tail
        # B-5a was built against is not the tail it will meet - B-4b got
        # in first. The list is tried newest first and the round refuses
        # if none of them matches, rather than guessing.
        for anchor in ("    '.bak_editink',\n]", "    '.bak_amber',\n]",
                       "    '.bak_pmlabels',\n]"):
            if rounds.count(fit(rounds, anchor)) == 1:
                rounds = rounds.replace(fit(rounds, anchor),
                                        fit(rounds, anchor[:-2] + NOTE + ']'),
                                        1)
                break
        else:
            raise SystemExit('B-5a: could not find the tail of ROUNDS')
        reg[ROUNDS] = rounds

        # ---- 2. the PS1 $suites list -------------------------------
        PS_NOTE = """    # B-5a, 8 Oct 2026 - the greys. Section 3 proves role picked
    # the token and not distance, section 4 is the fill/ink PAIR gate
    # B-4 did not have - fed B-4's own 9.77 -> 3.90 regression it
    # objects - and section 5 asserts what the round refused.
    '%s'
)""" % SUITE_NAME
        for anchor in ("    'test_pair_contrast.py'\n)",
                       "    'test_amber.py'\n)",
                       "    'test_passport_mobile.py'\n)"):
            if ps.count(fit(ps, anchor)) == 1:
                ps = ps.replace(fit(ps, anchor),
                                fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
                break
        else:
            raise SystemExit('B-5a: could not find the tail of $suites')
        reg[PS1] = ps

        # ---- 3. CR-1's census, all six numbers ---------------------
        # A round that changes a number owns every number that counts
        # it - in the patcher, never by hand. B-4 learnt this on the
        # gate with nothing staged.
        CR = os.path.join(ROOT, 'test_cssrules_outside.py')
        src = read(CR)
        # THE NOTE GOES ABOVE THE BLOCK, NEVER AFTER A VALUE. PM-1 made
        # that mistake in a tuple and it still parsed; B-4 made it in a
        # dict literal and swallowed three entries.
        CNOTE = ('# B-5a, 8 Oct 2026: 106 style= attribute literals and 50 in\n'
                 '# <script> became var(), so six of the numbers below came\n'
                 '# down with them. canvas 27 and unknown 91 did NOT - the\n'
                 '# round converted only what js_colour_context calls\n'
                 '# var-safe, and 203 - 85 = 118 = 27 + 91 says so.\n')
        for old, new2 in (
            ('MARKUP_STYLE = 224', 'MARKUP_STYLE = 118'),
            ('SCRIPT = 253', 'SCRIPT = 203'),
            ('PAGES = 47', 'PAGES = 40'),
            ("CTX = {'style-attr': 98, 'style-prop': 37, 'css-text': 0,",
             "CTX = {'style-attr': 61, 'style-prop': 24, 'css-text': 0,"),
            ('safe == 135', 'safe == 85'),
            ("   '139 of the 257 may become var() - and 118 may not, "
             "which is the whole '\n   'reason this round exists', safe)",
             "   '85 of the 203 may become var() - and 118 may not, "
             "which is the whole '\n   'reason this round exists. B-5a took "
             "50 of the safe ones and not '\n   'one of the 118, which is "
             "why that number has not moved', safe)"),
        ):
            if src.count(fit(src, old)) != 1:
                raise SystemExit('B-5a: %r in test_cssrules_outside.py '
                                 'matched %d time(s), not once'
                                 % (old, src.count(fit(src, old))))
            src = src.replace(fit(src, old), fit(src, new2), 1)
        src = src.replace(fit(src, 'MARKUP_STYLE = 118'),
                          fit(src, CNOTE + 'MARKUP_STYLE = 118'), 1)
        import ast as _ast
        try:
            _ast.parse(src)
        except SyntaxError as e:
            raise SystemExit('B-5a: test_cssrules_outside.py would not parse '
                             'after the census update - %s' % e)
        reg[CR] = src

        # ---- 4. alv_impact.COUNTERS --------------------------------
        # test_neutrals.py asserts numbers about the WHOLE tree, so a
        # later point round elsewhere can break it. B-4's push failed
        # on exactly that kind of suite because the previous two had
        # not added themselves here. This one adds itself.
        IMP = os.path.join(ROOT, 'alv_impact.py')
        isrc = read(IMP)
        # B-4b added itself here first, so the tail is its line now.
        OLD_C = ("    'test_pair_contrast.py',     # fill/ink pairs, whole "
                 "tree\n]")
        if isrc.count(fit(isrc, OLD_C)) != 1:
            OLD_C = "    'test_important_base.py',    # !important, whole tree\n]"
        NEW_C = (OLD_C[:-1] +
                 "    # B-5a, 8 Oct 2026 - adding itself, because its\n"
                 "    # sections 3 and 5 read every template in the tree.\n"
                 "    'test_neutrals.py',          # the greys, whole tree\n"
                 "]")
        if isrc.count(fit(isrc, OLD_C)) != 1:
            raise SystemExit('B-5a: the tail of COUNTERS matched %d time(s), '
                             'not once' % isrc.count(fit(isrc, OLD_C)))
        isrc = isrc.replace(fit(isrc, OLD_C), fit(isrc, NEW_C), 1)
        try:
            _ast.parse(isrc)
        except SyntaxError as e:
            raise SystemExit('B-5a: alv_impact.py would not parse - %s' % e)
        reg[IMP] = isrc

    print('B-5a  %d registry file(s) resolved, every anchor found' % len(reg))

    if CHECK:
        print('B-5a  NOT APPLIED')
        return 1

    # ---- NOW, and only now ----------------------------------------
    for p, new in planned.items():
        backup(p)
        write(p, new)
    for p, new in reg.items():
        backup(p)
        write(p, new)
    print('B-5a  CR-1 census updated: 224->118, 253->203, 47->40, '
          '98->61, 37->24, 135->85')
    print('B-5a  alv_impact.COUNTERS +1 (it adds itself)')
    print('B-5a  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
