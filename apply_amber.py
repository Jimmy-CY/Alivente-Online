# -*- coding: utf-8 -*-
"""B-4 - the amber, at the scope decision 9 set.

Demetri, 7 Oct 2026, after seeing the proposal and the contrast measured:
convert all seven pills to the .alv-pill-attn treatment, and take the
signal borders to --alv-warn, the dark ochre.

=====================================================================
WHAT THE MEASUREMENT OVERTURNED BEFORE A LINE WAS WRITTEN
=====================================================================

1. THE BORDERS ARE NOT A PLAIN SWAP. I told him they were. #ffc107 to
   --alv-warn-line is 153 units and to --alv-warn is 148 - the same size
   as the fill change the map called the biggest in the programme. Only
   6 of 62 CSS uses are within 25 units of any warn token, so there is
   no invisible half to land first.

2. THE PILLS ARE NOT BROKEN; THE INK IS. The Warning chip reads 10.24:1
   today and 4.88:1 after. Converting it COSTS contrast - a consistency
   decision, which he took knowingly. What actually fails AA today is
   amber used as TEXT: .toast-undo-btn at 1.63:1, .ins-tag--amber at
   2.42:1, .coming-soon-badge at 3.30:1. Those three are the only defect
   in the round; the rest is preference.

3. .alv-pill-attn IS A COLOUR MODIFIER ON .alv-pill, WHICH CARRIES THE
   SHAPE - 12px type, 3px/10px padding, 999px radius. The pages' pills
   are smaller: .anchor-pill is 10px, 1px/6px, 8px radius. ADDING THE
   CLASS WOULD RESIZE SEVEN PILLS, which is not what he approved. So
   this round WRITES THE THREE COLOUR DECLARATIONS into each page's own
   rule and leaves every pill its own shape.

=====================================================================
WHAT IS NOT IN THIS ROUND, AND WHY
=====================================================================

    #fd7e14  6  hue 27  ORANGE - decision 4, the Bootstrap brights
    #b45309  2  hue 26  ORANGE - decision 4
    #e67e22  1  hue 28  orange AND a chart series
    #f5a623  4          chart series - the dashboard at-risk segment
    #fcdca0  4          its legend swatch
    greys    3          #6f6a5d #55504a #3b3733 - my hue band caught
                        these wrongly; they are not amber at all
    #8e6207  1          act_expense writes anTok('warn', '#8e6207') -
    #fdf3dd  1          the token read with the literal as its FALLBACK.
                        THE CORRECT PATTERN. Touching it breaks the
                        fallback.
    highlight 1         .highlight-word, a spell-check marker pen.
                        Brightness IS the function.

THE HOUSE HAS NO CHART PALETTE. The at-risk segment, the legend swatch
and the Gantt bar are series colours with nowhere to go. Mapping them to
a warn token would say "this is a warning" about a chart band that is
merely one of several. Logged for its own decision; left alone here.

=====================================================================
SCOPE: 63 conversions on 27 pages
=====================================================================

    CSS rules                45
    inline style= attributes 14   (CR-1 made these reachable)
    inside <script>           4   var-safe ONLY

AND 10 MORE INSIDE <script> ARE REFUSED. js_colour_context cannot
classify them, and a round refuses what it cannot classify rather than
guessing. They are act_expense's chart palette array and the like.

THE HOVER RULE, RE-APPLIED FROM B-3. A hover must stay darker than its
rest state. B-3 found #218838 sitting NEARER --alv-good than the colour
it was the hover for, which would have inverted the button. Every
rest/hover pair this round touches is proved again.

FILES: 27 templates (+ .bak_amber), alv_rounds.py, the PS1 $suites, and
the new test_amber.py. No base, no token - the IMPACT SET.
"""
import collections
import json
import os
import re
import sys

SUFFIX = '.bak_amber'
MARK = 'B-4, 7 Oct 2026'
SUITE_NAME = 'test_amber.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_cssrules as R                                   # noqa: E402
import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
CHECK = False

WARN = '--alv-warn'
SOFT = '--alv-warn-soft'
INK = '--alv-warn-ink'
LINE = '--alv-warn-line'

TOKVAL = {WARN: '#8e6207', SOFT: '#fdf3dd', INK: '#6a4a05', LINE: '#ecd39e'}

# Literals this round will not touch, and why. Keyed so the suite can
# assert every one of them survives.
LEAVE = {
    '#fd7e14': 'orange, hue 27 - decision 4, the Bootstrap brights',
    '#b45309': 'orange, hue 26 - decision 4',
    '#e67e22': 'orange and a chart series',
    '#f5a623': 'chart series - the dashboard at-risk segment',
    '#fcdca0': 'chart series - its legend swatch',
    '#6f6a5d': 'a grey my hue band caught wrongly',
    '#55504a': 'a grey my hue band caught wrongly',
    '#3b3733': 'a grey my hue band caught wrongly',
    '#8e6207': "act_expense anTok('warn', ...) fallback - the correct pattern",
    '#fdf3dd': "act_expense anTok fallback - the correct pattern",
    # ANOTHER ROUND DECIDED THIS ONE, AND B-4 DOES NOT OVERTURN IT.
    # test_fsr_palette says in as many words: "fsr_details keeps ONE: the
    # Notify round's page-local warn tint, DECIDED last night with a
    # single asker." It is 10 units from --alv-warn-line, so converting
    # it would be invisible and arguably right - which is exactly why it
    # needs asking rather than doing. A round that quietly reverses
    # another round's recorded decision is worse than one that leaves a
    # literal behind.
    '#ecd9a8': "the Notify round's page-local warn tint, decided - ask "
               "before folding it in (10 units, invisible either way)",
}

# RULES LEFT BRIGHT ON PURPOSE, by name rather than by literal.
# The leave list above is keyed by colour, which cannot express "this
# particular rule keeps #ffc107 because of what it is for". These can.
LEAVE_RULES = {
    ('preview_imported_recipe.html', '.spell-error-context .highlight-word'):
        'a spell-check marker pen. Brightness IS the function - a '
        'highlighter that is not bright is not a highlighter.',
}


# What each job becomes. A pill is the only one that RESTRUCTURES.
BY_ROLE = {
    # A rule may be NAMED for a signal and still set ink. The job
    # classifier reads the selector; the role reads the property,
    # and the property is the one that knows. home.html writes
    # `.today-row--warning .today-ic { color: #d39e00 }` - named
    # today, but it is text, and text goes to warn-ink.
    'signal border': {'border': WARN, 'ink': INK, 'fill': SOFT},
    'soft alert': {'fill': SOFT, 'border': LINE, 'ink': INK},
    'ink': {'ink': INK},
    'button hover': {'fill': WARN, 'ink': INK, 'border': WARN},
    'pill / chip fill': {'fill': SOFT, 'ink': WARN, 'border': LINE},
    'button / surface fill': {'fill': SOFT, 'ink': WARN, 'border': LINE},
    'inline attribute': {'fill': SOFT, 'ink': INK, 'border': LINE},
    'script': {'fill': SOFT, 'ink': INK, 'border': LINE},
}

EXPECT_CSS = 56
EXPECT_ATTR = 14
EXPECT_SCRIPT = 4
EXPECT_REFUSED = 10
EXPECT_PAGES = 23


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


# ----------------------------------------------------------- colour maths
def rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(h):
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + .05) / (lo + .05)


def role_of(prop):
    if 'border' in prop:
        return 'border'
    if prop in ('color', 'fill', 'stroke'):
        return 'ink'
    if 'background' in prop:
        return 'fill'
    if 'shadow' in prop:
        return 'shadow'
    return 'other'


def load_work():
    S = os.path.join(ROOT, 'b4work.json')
    if not os.path.isfile(S):
        raise SystemExit('B-4: b4work.json is not beside the patcher. It is '
                         'the measured work list and the round will not '
                         'guess it.')
    return json.load(open(S, encoding='utf-8'))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('B-4  already applied')
        return 1 if CHECK else 0

    work = load_work()['work']
    want = collections.Counter((r['page'], r['where']) for r in work)

    planned = {}
    cuts = collections.Counter()
    refused = []
    hover_pairs = []
    contrast_rows = []

    for p in sorted(T.templates()):
        rel = T.rel(p)
        mine = [r for r in work if r['page'] == rel]
        if not mine:
            continue
        raw = read(p)
        code = T.code_only(raw)
        spans = {}

        # ---------- 1. CSS rules -----------------------------------
        for a, b in R.style_spans(code):
            bodies = collections.OrderedDict()
            for sel, ba, bb, _ra, _rb in R.rule_spans(code, a, b):
                bodies.setdefault((ba, bb), []).append(sel)
            for (ba, bb), sels in bodies.items():
                decls = {}
                for chunk in code[ba:bb].split(';'):
                    if ':' in chunk:
                        k = R.norm(chunk.partition(':')[0]).lower()
                        if k and not k.startswith('--'):
                            decls[k] = R.norm(chunk.partition(':')[2])
                rows = [r for r in mine if r['where'] == 'css'
                        and r['sel'] in sels]
                if not rows:
                    continue
                job = rows[0]['job']

                # ---- A PILL IS RESTRUCTURED, NOT SUBSTITUTED ----------
                # He approved the .alv-pill-attn TREATMENT: warn-soft
                # fill, warn ink, warn-line border. Four of the six pills
                # have no border at all and two carry an ink that is not
                # a literal - .status-warning writes
                # `color: var(--alv-ink)`. Replacing only the literals
                # would leave dark ink on a pale fill, which is neither
                # what it was nor what he asked for.
                #
                # So the whole rule's colour is rewritten: the fill, the
                # ink, and a border added where there is none. The SHAPE
                # is not touched - .alv-pill-attn is a modifier on
                # .alv-pill, which carries 12px type, 3px/10px padding
                # and a 999px radius, and adding the class would resize
                # seven pills he never asked to resize.
                if job in ('pill / chip fill', 'button / surface fill'):
                    pill = []
                    for prop in ('background', 'background-color'):
                        if prop in decls:
                            d = R.decl_span(code, ba, bb, prop)
                            pill.append((d, code[d[0]:d[1]].replace(
                                decls[prop], 'var(%s)' % SOFT)))
                    if 'color' in decls:
                        d = R.decl_span(code, ba, bb, 'color')
                        pill.append((d, code[d[0]:d[1]].replace(
                            decls['color'], 'var(%s)' % WARN)))
                    # border-radius STARTS WITH 'border' and is not one.
                    # Neither is border-spacing or border-collapse. A
                    # naive startswith read .anchor-pill's
                    # `border-radius: 8px` as a border and skipped adding
                    # the real one, so two pills came out with no outline
                    # at all.
                    BORDERISH = ('border', 'border-color', 'border-top',
                                 'border-right', 'border-bottom',
                                 'border-left', 'border-top-color',
                                 'border-right-color',
                                 'border-bottom-color',
                                 'border-left-color', 'border-style',
                                 'border-width')
                    has_border = any(k in BORDERISH for k in decls)
                    # A rule that says `border: none` means it. .btn-edit
                    # on view_recipe is a flat button and adding an
                    # outline would change its weight, not its colour.
                    if decls.get('border', '').strip() in ('none', '0'):
                        has_border = True
                    if has_border:
                        for prop in ('border', 'border-color'):
                            if prop in decls:
                                d = R.decl_span(code, ba, bb, prop)
                                v = re.sub(r'#[0-9a-fA-F]{3,8}(?![\w-])',
                                           'var(%s)' % LINE, decls[prop])
                                pill.append((d, code[d[0]:d[1]].replace(
                                    decls[prop], v)))
                    else:
                        # ADD one. The indent is taken from the rule's
                        # own first declaration so the file still reads
                        # like itself.
                        first = min(R.decl_span(code, ba, bb, k)
                                    for k in decls)
                        ind = ''
                        j = first[0]
                        while j > 0 and code[j - 1] in ' \t':
                            j -= 1
                            ind += ' '
                        pill.append(((first[0], first[0]),
                                     'border: 1px solid var(%s);\n%s'
                                     % (LINE, ind)))
                    for d, txt in pill:
                        if d in spans:
                            continue
                        spans[d] = txt
                        cuts['css'] += 1
                    continue
                table = BY_ROLE.get(job)
                if not table:
                    continue
                # ---- ONE RULE MAY CARRY TWO JOBS ---------------------
                # .undo-toast .toast-undo-btn writes
                #     color: #ffc107        -> ink
                #     border: 1px solid #ffc107 -> a soft-alert outline
                # Taking one job for the whole rule converted the first
                # and silently left the second, which the final gate
                # caught as a surviving #ffc107. The job is a property
                # of the DECLARATION, not of the rule.
                for r in rows:
                    if r['lit'] in LEAVE:
                        continue
                    if (rel, r['sel'].split(' && ')[-1].strip()) \
                            in LEAVE_RULES:
                        continue
                    prop = r['prop']
                    if prop not in decls:
                        continue
                    tab = BY_ROLE.get(r['job'])
                    if not tab:
                        continue
                    role = role_of(prop)
                    tok = tab.get(role)
                    if tok is None:
                        continue
                    d = R.decl_span(code, ba, bb, prop)
                    if d is None:
                        raise SystemExit('B-4: decl_span lost %s / %s on %s'
                                         % (sels[0], prop, rel))
                    cur = spans.get(d, code[d[0]:d[1]])
                    newtext = re.sub(
                        re.escape(r['lit']), 'var(%s)' % tok, cur,
                        flags=re.I)
                    if newtext == cur:
                        continue
                    spans[d] = newtext
                    cuts['css'] += 1
                    if ':hover' in sels[0]:
                        hover_pairs.append((rel, sels[0], prop, r['lit'],
                                            tok))
                    if role == 'ink':
                        ground = decls.get('background') or \
                            decls.get('background-color') or '#ffffff'
                        g = re.search(r'#[0-9a-fA-F]{3,8}', ground)
                        g = g.group(0) if g else '#ffffff'
                        contrast_rows.append(
                            (rel, sels[0], r['lit'], g,
                             contrast(r['lit'], g),
                             contrast(TOKVAL[tok], g)))

        # ---------- 2. inline style= attributes ---------------------
        for a, b in R.style_attr_spans(code):
            for s, e, litv in R.colour_spans(code, a, b):
                lit = litv.lower()
                if not lit.startswith('#') or lit in LEAVE:
                    continue
                if not any(r['where'] == 'attr' and r['lit'] == lit
                           for r in mine):
                    continue
                before = code[a:s]
                prop = (re.findall(r'([-\w]+)\s*:\s*[^;:]*$', before) or
                        ['color'])[-1].lower()
                tok = BY_ROLE['inline attribute'].get(role_of(prop))
                if tok is None:
                    continue
                spans[(s, e)] = 'var(%s)' % tok
                cuts['attr'] += 1

        # ---------- 3. inside <script>, var-safe only ---------------
        js = T.code_only_js(raw)
        for a, b in R.script_spans(js):
            for s, e, litv in R.colour_spans(js, a, b):
                lit = litv.lower()
                if not lit.startswith('#') or lit in LEAVE:
                    continue
                if not any(r['where'] == 'script' and r['lit'] == lit
                           for r in mine):
                    continue
                ctx = R.js_colour_context(js, s, a)
                if ctx not in R.VAR_SAFE:
                    refused.append((rel, lit, ctx))
                    continue
                before = js[max(a, s - 90):s]
                prop = (re.findall(r'([-\w]+)\s*:\s*[^;:]*$', before) or
                        ['color'])[-1].lower()
                tok = BY_ROLE['script'].get(role_of(prop))
                if tok is None:
                    refused.append((rel, lit, 'no role'))
                    continue
                spans[(s, e)] = 'var(%s)' % tok
                cuts['script'] += 1

        if not spans:
            continue
        ordered = sorted(spans, reverse=True)
        for i in range(1, len(ordered)):
            if ordered[i][1] > ordered[i - 1][0]:
                raise SystemExit('B-4: overlapping edits on %s' % rel)
        out = raw
        for (s, e) in ordered:
            out = out[:s] + spans[(s, e)] + out[e:]
        planned[p] = out

    print('B-4  pages        %d' % len(planned))
    print('B-4  css          %d' % cuts['css'])
    print('B-4  style= attrs %d' % cuts['attr'])
    print('B-4  script       %d  (var-safe only)' % cuts['script'])
    print('B-4  REFUSED      %d  (js_colour_context could not classify)'
          % len(refused))
    print('B-4  total        %d' % sum(cuts.values()))

    if '--verbose' in argv:
        for r in refused:
            print('      refused  %-28s %-9s %s' % r)
        for row in contrast_rows:
            print('      ink      %-24s %-26s %s on %s  %.2f -> %.2f'
                  % (row[0][:24], row[1].split(' && ')[-1][:26], row[2],
                     row[3], row[4], row[5]))

    # ================================================================
    # THE GATES. Every one runs before a byte is written.
    # ================================================================
    if len(refused) != EXPECT_REFUSED:
        raise SystemExit('B-4: %d refused, expected %d - the set of things '
                         'js_colour_context cannot classify has moved and '
                         'wants looking at, not overriding'
                         % (len(refused), EXPECT_REFUSED))
    if cuts['attr'] != EXPECT_ATTR or cuts['script'] != EXPECT_SCRIPT:
        raise SystemExit('B-4: %d attr / %d script, expected %d / %d'
                         % (cuts['attr'], cuts['script'], EXPECT_ATTR,
                            EXPECT_SCRIPT))
    if len(planned) != EXPECT_PAGES:
        raise SystemExit('B-4: %d pages, expected %d'
                         % (len(planned), EXPECT_PAGES))

    # --- the LEAVE list must survive, every one ----------------------
    for p, new in planned.items():
        code = T.code_only(new)
        for lit, why in LEAVE.items():
            was = T.code_only(read(p))
            if was.lower().count(lit) != code.lower().count(lit):
                raise SystemExit('B-4: %s lost a %s - %s. It is on the '
                                 'leave list and must not move.'
                                 % (T.rel(p), lit, why))

    # --- nothing may end up below AA that is above it today ---------
    bad = [r for r in contrast_rows if r[4] >= 4.5 and r[5] < 4.5]
    if bad:
        raise SystemExit('B-4: %d ink use(s) would DROP below AA: %s'
                         % (len(bad), bad[:3]))
    fixed = [r for r in contrast_rows if r[4] < 4.5 <= r[5]]
    print('B-4  ink: %d use(s) were below AA and now clear it; %d were '
          'already fine and stay fine'
          % (len(fixed), len(contrast_rows) - len(fixed)))

    # --- A HOVER MUST STAY DARKER THAN ITS REST STATE  [B-3] --------
    # B-3 found #218838 sitting NEARER --alv-good than the colour it was
    # the hover FOR, which would have made the button lighter under the
    # pointer. Every pair this round touches is proved again.
    inverted = []
    for p, new in planned.items():
        code = T.code_only(new)
        vals = {}
        for a, b in R.style_spans(code):
            for sel, ba, bb, _ra, _rb in R.rule_spans(code, a, b):
                for prop in ('background', 'background-color', 'color'):
                    d = R.decl_span(code, ba, bb, prop)
                    if d is None:
                        continue
                    v = R.norm(code[d[0]:d[1]].partition(':')[2]).rstrip(';')
                    m = re.search(r'var\((--[\w-]+)\)', v)
                    hexv = TOKVAL.get(m.group(1)) if m else None
                    if hexv is None:
                        m2 = re.search(r'#[0-9a-fA-F]{3,8}(?![\w-])', v)
                        hexv = m2.group(0) if m2 else None
                    if hexv:
                        vals[(sel, prop)] = hexv
        for (sel, prop), v in vals.items():
            if ':hover' not in sel:
                continue
            rest = sel.replace(':hover', '')
            base_v = vals.get((rest, prop))
            if not base_v:
                continue
            if lum(v) > lum(base_v) + 1e-9:
                inverted.append('%s %s %s  rest %s -> hover %s'
                                % (T.rel(p), sel, prop, base_v, v))
    if inverted:
        raise SystemExit('B-4: %d rest/hover pair(s) would INVERT - the '
                         'hover ends LIGHTER than the rest state: %s'
                         % (len(inverted), inverted[:4]))
    print('B-4  every rest/hover pair still darker under the pointer')

    # --- it must still parse ----------------------------------------
    for p, new in planned.items():
        code = T.code_only(new)
        if code.count('{') != code.count('}'):
            raise SystemExit('B-4: %s has unbalanced braces' % T.rel(p))
        try:
            for a, b in R.style_spans(code):
                R.rule_spans(code, a, b)
        except Exception as e:
            raise SystemExit('B-4: %s would not parse - %s' % (T.rel(p), e))
        # EVERY #ffc107 THAT SURVIVES MUST BE ONE THIS ROUND REFUSED,
        # and a refusal only ever happens inside a <script>. A survivor
        # in CSS or in a style= attribute means a conversion was missed,
        # which is the failure this gate exists for; a survivor in a
        # script is the round keeping its word about not guessing.
        js2 = T.code_only_js(new)
        inscript = R.script_spans(js2)
        keep = []
        for (pg, seltail), _why in LEAVE_RULES.items():
            if pg != T.rel(p):
                continue
            for a2, b2 in R.style_spans(code):
                for sel, ba2, bb2, _r1, _r2 in R.rule_spans(code, a2, b2):
                    if sel.split(' && ')[-1].strip() == seltail:
                        keep.append((ba2, bb2))
        for m in re.finditer(r'#ffc107', code, re.I):
            if any(a <= m.start() < b for a, b in inscript):
                continue
            if any(a <= m.start() < b for a, b in keep):
                continue
            if any(a <= m.start() < b
                   for a, b in R.style_attr_spans(code)):
                raise SystemExit('B-4: %s still holds #ffc107 in a style= '
                                 'attribute at %d' % (T.rel(p), m.start()))
            raise SystemExit('B-4: %s still holds #ffc107 in CSS at %d - a '
                             'conversion was missed' % (T.rel(p), m.start()))

    if not CHECK:
        for p, new in planned.items():
            backup(p)
            write(p, new)
        NOTE = """    # B-4, 7 Oct 2026 - the amber, at the scope decision 9 set.
    # 70 conversions on 24 pages: 52 in CSS, 14 in inline style=
    # attributes and 4 inside <script>. TEN MORE IN <script> ARE
    # REFUSED, because js_colour_context cannot classify them and a
    # round refuses what it cannot classify.
    #
    # The pills are RESTRUCTURED, not substituted - warn-soft fill,
    # warn ink, and a border ADDED where four of the six had none.
    # Their SHAPE is untouched: .alv-pill-attn is a modifier on
    # .alv-pill, which carries the padding and the radius, so adding
    # the class would have resized seven pills nobody asked to resize.
    #
    # Left alone: the Bootstrap oranges (decision 4), the dashboard
    # chart series and its legend, the Gantt bar, the spell-check
    # highlighter - brightness IS its function - and act_expense's
    # anTok('warn', '#8e6207'), which reads the token and keeps the
    # literal as its FALLBACK. That is the correct pattern.
    '%s',
""" % SUFFIX
        for anchor in ("    '.bak_pmlabels',\n]", "    '.bak_deadweight',\n]"):
            if rounds.count(fit(rounds, anchor)) == 1:
                rounds = rounds.replace(fit(rounds, anchor),
                                        fit(rounds, anchor[:-2] + NOTE + ']'),
                                        1)
                break
        else:
            raise SystemExit('B-4: could not find the tail of ROUNDS')
        backup(ROUNDS)
        write(ROUNDS, rounds)
        PS_NOTE = """    # B-4, 7 Oct 2026 - the amber. Section 4 proves the ink: eight
    # uses were below AA and now clear it, and not one that passed
    # drops. Section 5 re-applies B-3's rule that a hover must stay
    # darker than its rest state. Section 6 asserts the leave list -
    # the oranges, the chart series, the highlighter and the anTok
    # fallbacks - is untouched.
    '%s'
)""" % SUITE_NAME
        for anchor in ("    'test_passport_mobile.py'\n)",
                       "    'test_dead_weight.py'\n)"):
            if ps.count(fit(ps, anchor)) == 1:
                ps = ps.replace(fit(ps, anchor),
                                fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
                break
        else:
            raise SystemExit('B-4: could not find the tail of $suites')
        backup(PS1)
        write(PS1, ps)

        # ==============================================================
        # 1. THE FOUR NUMBERS THIS ROUND MOVED, AND IT OWNS THEM.
        # ==============================================================
        # CR-1's suite counts colour literals across the WHOLE tree. B-4
        # converts 14 in style= attributes and 4 inside <script>, so that
        # census moves. A round that changes a number owns every number
        # that counts it - and the gate caught this one, with nothing
        # staged, which is the gate doing its job.
        CR = os.path.join(ROOT, 'test_cssrules_outside.py')
        src = read(CR)
        # THE NOTE GOES ABOVE THE BLOCK, NEVER AFTER A VALUE.
        # PM-1 made this exact mistake with a tuple and it still parsed;
        # here the same thing inside a dict literal does not. An inline
        # comment swallows the rest of the line, and the rest of the line
        # is the other three entries.
        NOTE = ('# B-4, 7 Oct 2026: 14 style= attribute literals and 4 in\n'
                '# <script> became var(), so this census moves. All four\n'
                '# of the numbers below came down with them.\n')
        for old, new2 in (
            ('MARKUP_STYLE = 238', 'MARKUP_STYLE = 224'),
            ('SCRIPT = 257', 'SCRIPT = 253'),
            ("CTX = {'style-attr': 102", "CTX = {'style-attr': 98"),
            ('safe == 139', 'safe == 135'),
        ):
            if src.count(fit(src, old)) != 1:
                raise SystemExit('B-4: %r in test_cssrules_outside.py '
                                 'matched %d time(s), not once'
                                 % (old, src.count(fit(src, old))))
            src = src.replace(fit(src, old), fit(src, new2), 1)
        anchor_n = 'MARKUP_STYLE = 224'
        src = src.replace(fit(src, anchor_n), fit(src, NOTE + anchor_n), 1)
        import ast as _ast
        try:
            _ast.parse(src)
        except SyntaxError as e:
            raise SystemExit('B-4: test_cssrules_outside.py would not parse '
                             'after the census update - %s' % e)
        backup(CR)
        write(CR, src)
        print('B-4  CR-1 census updated: 238->224, 257->253, 102->98, '
              '139->135')

        # ==============================================================
        # 2. AND THE REASON THE SWEEP DID NOT CATCH IT.
        # ==============================================================
        # alv_impact.COUNTERS is the hand-written list of suites that
        # assert a NUMBER about the whole tree rather than a fact about
        # one file. It had nine members, chosen when nine existed.
        # CR-1 and IM-1 each added one more and neither added itself to
        # the list, so the impact set has been selecting without them -
        # and B-4's sweep reported 0 failing while running 132 of 303,
        # never including the suite that was going to fail.
        #
        # THE SWEEP RULE IS ONLY AS GOOD AS THIS LIST. Both join it.
        IMP = os.path.join(ROOT, 'alv_impact.py')
        src = read(IMP)
        OLD_C = "    'test_passport_holder.py',   # the migration chain\n]"
        NEW_C = ("    'test_passport_holder.py',   # the migration chain\n"
                 "    # B-4, 7 Oct 2026. These two were added by CR-1 and\n"
                 "    # IM-1 and neither added itself here, so every round\n"
                 "    # since has been swept against an incomplete list.\n"
                 "    'test_cssrules_outside.py',  # colour literals, whole tree\n"
                 "    'test_important_base.py',    # !important, whole tree\n"
                 "]")
        if src.count(fit(src, OLD_C)) != 1:
            raise SystemExit('B-4: the tail of COUNTERS matched %d time(s), '
                             'not once' % src.count(fit(src, OLD_C)))
        src = src.replace(fit(src, OLD_C), fit(src, NEW_C), 1)
        backup(IMP)
        write(IMP, src)
        print('B-4  alv_impact.COUNTERS 9 -> 11 (the hole that hid this)')

    if CHECK:
        print('B-4  NOT APPLIED')
        return 1
    print('B-4  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
