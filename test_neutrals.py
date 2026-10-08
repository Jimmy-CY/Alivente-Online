# -*- coding: utf-8 -*-
"""test_neutrals.py - Section B round B-5a, 8 Oct 2026.

Decision 2: "Convert the greys to the house ink ramp; leave #000000
alone until I survey it." S-a is that survey and it is done, so the
black half is settled and this round is the greys - tiers A and B only.

THE SHAPE OF THIS ROUND IS THE ARGUMENT FOR DECISION 9.

    inline style= attributes  106
    inside <script>            50
    page stylesheets            2

B-1, B-2 and B-2b already took the greys out of the stylesheets. TWO are
left there. Everything else is in markup and JavaScript, which Section B
could not see at all until CR-1.

=====================================================================
SECTION 3 IS THE ROUND: ROLE PICKS THE TOKEN, DISTANCE ONLY BREAKS TIES
=====================================================================

The first version of this map chose purely by distance and got twelve of
170 semantically wrong:

    color: #dee2e6   ->  var(--alv-line)    a LINE token used as ink
    color: #fff      ->  var(--alv-paper)   a SURFACE token used as ink

Both are the right COLOUR and the wrong NAME, and the name is the
meaning: somebody later retuning --alv-line would be moving text rather
than a hairline. Rebuilt role-first, #fff as ink correctly takes
--alv-on-accent, and #dee2e6 as ink leaves this round entirely.

AND THE SAME LITERAL CAN SIT IN TWO TIERS AT ONCE. #6c757d as ink is
16.8 units from --alv-neutral - tier B, invisible. As a BORDER the
nearest line token is far enough to be tier C. Distance alone cannot see
that. Section 7 proves the patcher keys on (literal, role) and not on
the literal, because a dict keyed on the literal collapses the two and
converts the border with the ink token - the same fault, put back by the
patcher after the map had removed it.

=====================================================================
SECTION 4 IS THE GATE B-4 DID NOT HAVE
=====================================================================

B-4 checked that every INK conversion improved contrast. It never
checked a FILL conversion against the ink already sitting on it, so
.btn-edit:hover went from 9.77:1 to 3.90:1 - the background moved to
dark ochre and the #000 ink stayed where it was. One failure in 26
pairs, found by reading the result rather than by the gate.

This round evaluates the PAIR, and section 4 feeds the gate B-4's exact
regression to show it objects.

WHAT IS LEFT ALONE: 19 blacks that S-a settled, 5 canvas literals - a 2D
context cannot resolve a custom property - and 9 the classifier cannot
name. Tier C is 100 uses, 19 of which are that same black, so 81 go to
B-5b with renders, because the colour map says the render IS that
decision.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_neutrals'
ME = 'test_neutrals.py'
PATCHER = 'apply_neutrals.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'B-5a, 8 Oct 2026'

EXPECT_CUTS = 158
EXPECT_PAGES = 32
EXPECT_CANVAS = 5
EXPECT_UNKNOWN = 9

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                       # noqa: E402
import alv_cssrules as R                                   # noqa: E402
import alv_rounds as RD                                    # noqa: E402
import apply_neutrals as N                                 # noqa: E402

TOUCHED = sorted(p for p in T.templates() if os.path.isfile(p + SUFFIX))


def left(p):
    """The page AS THIS ROUND LEFT IT, not as it stands now.

    PM-1 taught test_dead_weight.py this and B-4b is about to need it
    here: it takes the #000 off .btn-edit:hover on view_recipe.html,
    which is one of this round's 32 pages, and section 6 asserts every
    #000 on those pages survived B-5a. Read against the live file that
    goes red when a LATER round does its own job correctly - which is a
    suite failing for being out of date rather than for a fault, and
    the worst kind of red there is.

    Sections 3 and 5 deliberately do NOT use this. They are whole-tree
    census claims, they are what put this suite in alv_impact.COUNTERS,
    and they are supposed to move when the tree moves.
    """
    return RD.as_left_by(p, SUFFIX, read)


# ==========================================================================
head('1. SCOPE - AND WHY IT IS ALMOST ALL MARKUP AND SCRIPT')
# ==========================================================================
ok(len(TOUCHED) == EXPECT_PAGES, '%d pages' % EXPECT_PAGES,
   [T.rel(p) for p in TOUCHED])
stand = set(T.standalone())
ok(not [p for p in TOUCHED if T.rel(p) in stand],
   'and not one standalone template - they have no :root to read')
in_css = in_attr = in_js = 0
for p in TOUCHED:
    was, now = T.code_only(read(p + SUFFIX)), T.code_only(left(p))
    wjs, njs = T.code_only_js(read(p + SUFFIX)), T.code_only_js(left(p))
    in_css += sum(now[a:b].count('var(--alv-')
                  for a, b in R.style_spans(now)) - \
        sum(was[a:b].count('var(--alv-') for a, b in R.style_spans(was))
    in_attr += sum(now[a:b].count('var(--alv-')
                   for a, b in R.style_attr_spans(now)) - \
        sum(was[a:b].count('var(--alv-') for a, b in R.style_attr_spans(was))
    in_js += sum(njs[a:b].count('var(--alv-')
                 for a, b in R.script_spans(njs)) - \
        sum(wjs[a:b].count('var(--alv-') for a, b in R.script_spans(wjs))
ok(in_attr > in_css and in_js > in_css,
   'MORE tokens were written into markup (%d) and script (%d) than into '
   'stylesheets (%d) - B-1/B-2/B-2b already took the greys out of the CSS'
   % (in_attr, in_js, in_css))
ok(in_css <= 4,
   '  only %d landed in a <style> block, which is the whole case for '
   'decision 9' % in_css, in_css)


# ==========================================================================
head('2. THE TIERS - A IS EXACT, B IS WITHIN 25 UNITS')
# ==========================================================================
ok(N.rgb('#f8f9fa') == N.rgb(N.TOKVAL['--alv-surface']),
   '#f8f9fa IS --alv-surface, to the byte - tier A')
ok(N.rgb('#e9ecef') == N.rgb(N.TOKVAL['--alv-surface-deep']),
   '#e9ecef IS --alv-surface-deep - tier A')


def dist(a, b):
    x, y = N.rgb(a), N.rgb(b)
    return sum((p - q) ** 2 for p, q in zip(x, y)) ** 0.5


ok(dist('#6c757d', N.TOKVAL['--alv-neutral']) <= 25,
   '#6c757d is %.1f units from --alv-neutral - tier B, invisible'
   % dist('#6c757d', N.TOKVAL['--alv-neutral']))
ok(dist('#adb5bd', N.TOKVAL['--alv-ink-faint']) > 25,
   '#adb5bd is %.1f units from the nearest ink token - TIER C, and not in '
   'this round' % dist('#adb5bd', N.TOKVAL['--alv-ink-faint']))


# ==========================================================================
head('3. ROLE PICKS THE TOKEN - THE CLAIM THIS ROUND IS BUILT ON')
# ==========================================================================
ok(N.role_of('color') == 'ink', 'color is ink')
ok(N.role_of('background-color') == 'fill',
   'background-color is a FILL, not ink - it ends in "color" and the test '
   'must not be fooled by that')
ok(N.role_of('border-color') == 'border',
   'and border-color is a border, for the same reason')
# border-radius starts with "border" and B-4 was fooled by exactly that -
# it read a radius as a border and two pills got no outline. role_of puts
# it in the border family, which is harmless here because no radius
# carries a colour, but the next round to ask "has this rule a border?"
# must test the PROPERTY NAME against a list and not a prefix.
ok(N.role_of('color') != N.role_of('background-color'),
   'ink and fill are different roles, so one literal in both places gets '
   'two different tokens - which is the point of the whole map')
# #fff as INK must be --alv-on-accent, never --alv-paper
white_ink = [p for p in TOUCHED
             if re.search(r'color:\s*var\(--alv-on-accent\)', left(p))]
ok(white_ink,
   'white used as INK takes --alv-on-accent, not --alv-paper - the colour '
   'is identical and the NAME is the meaning',
   [T.rel(p) for p in white_ink][:4])
# #dee2e6 as INK must NOT have been converted
leftover = []
for p in TOUCHED + [q for q in T.templates() if q not in TOUCHED]:
    code = T.code_only(read(p))
    for a, b in R.style_spans(code):
        for sel, ba, bb, _r, _s in R.rule_spans(code, a, b):
            d = R.decl_span(code, ba, bb, 'color')
            if d and '#dee2e6' in code[d[0]:d[1]].lower():
                leftover.append('%s %s' % (T.rel(p), sel.split(' && ')[-1]))
ok(len(leftover) >= 8,
   '#dee2e6 used as INK is STILL a literal on %d rules - the colour map '
   'says that one "wants looking at, not mapping", and a distance-only '
   'map had quietly converted all of them' % len(leftover), leftover[:3])


# ==========================================================================
head('4. THE PAIR GATE - AND IT CATCHES B-4 EXACT REGRESSION')
# ==========================================================================
worse = []
pairs = 0
for p in TOUCHED:
    was = N.pair_table(T.code_only(read(p + SUFFIX)))
    now = N.pair_table(T.code_only(left(p)))
    for sel, (bg, ink) in now.items():
        if sel not in was:
            continue
        a1, a2 = N.contrast(*was[sel]), N.contrast(bg, ink)
        if a1 is None or a2 is None:
            continue
        pairs += 1
        if a2 < 4.5 and a2 < a1 - 0.01:
            worse.append('%s %s %.2f -> %.2f' % (T.rel(p), sel, a1, a2))
ok(not worse,
   '%d fill/ink pair(s) compared, not one drops below AA' % pairs, worse[:4])
ok(pairs >= 40, '  and there are pairs to compare', pairs)
# THE CONTROL. B-4's .btn-edit:hover went 9.77 -> 3.90 because the fill
# moved and the ink did not. Fed to this gate, it must object.
b4 = N.contrast('#8e6207', '#000000')
ok(b4 < 4.5 and b4 < N.contrast('#e0a800', '#000000'),
   'CONTROL: fed B-4 .btn-edit:hover (%.2f -> %.2f) the gate objects'
   % (N.contrast('#e0a800', '#000000'), b4))
ok(not (N.contrast('#ffffff', '#6a4a05') < 4.5),
   '  and a pair that merely improves does not trip it')


# ==========================================================================
head('5. WHAT THE ROUND REFUSED')
# ==========================================================================
canvas = unknown = 0
for p in T.templates():
    js = T.code_only_js(read(p))
    for a, b in R.script_spans(js):
        for s, _e, l in R.colour_spans(js, a, b):
            if not l.startswith('#') or not N.rgb(l):
                continue
            c = N.rgb(l)
            if max(c) - min(c) > 22:
                continue
            k = R.js_colour_context(js, s, a)
            if k == 'canvas':
                canvas += 1
            elif k == 'unknown':
                unknown += 1
ok(canvas >= EXPECT_CANVAS,
   'at least %d neutral(s) inside <script> are a CANVAS colour and stay '
   'literal - a 2D context cannot resolve a custom property and the chart '
   'would vanish' % EXPECT_CANVAS, canvas)
ok(unknown >= EXPECT_UNKNOWN,
   'and at least %d cannot be classified, so the round refuses them'
   % EXPECT_UNKNOWN, unknown)
ok('canvas' not in R.VAR_SAFE, '  canvas is not var-safe, and says so')


# ==========================================================================
head('5b. EVERY TOKEN IT WROTE EXISTS - AND RESOLVES WHERE IT WROTE IT')
# ==========================================================================
# A var() naming a token base has not got is an INVALID declaration. The
# property falls back to what it inherits and nothing says so: no parse
# error, no console warning, just the wrong colour on a page nobody
# opened. Base carries its tokens in TWO :root rules and a map built
# from the first one alone is six short - which is how this came to be
# a check rather than an assumption.
have = N.base_tokens()
wrote = set()
for p in TOUCHED:
    was, now = read(p + SUFFIX), left(p)
    for t in re.findall(r'var\((--alv-[\w-]+)\)', now):
        if now.count('var(%s)' % t) > was.count('var(%s)' % t):
            wrote.add(t)
ok(wrote, 'the round wrote %d distinct token(s)' % len(wrote), sorted(wrote))
absent = sorted(t for t in wrote if t not in have)
ok(not absent, '  and base declares every one of them on :root', absent)
ok(len(have) >= 80,
   '  base declares %d tokens, across TWO :root rules - one rule is not '
   'the map' % len(have))
# AND THE CSSOM. 12 of the 50 script conversions are not HTML strings at
# all, they are el.style.prop = 'var(...)' and one el.style.cssText. A
# canvas cannot resolve a custom property and the round refused those;
# whether the CSSOM can is a browser question, and it was asked - all 16
# forms, at desktop and phone, resolved to the token value. See
# scratchpad/b5browser.py and the delivery note. What CAN be asserted
# here is that not one of them is read back.
backs = []
for p in TOUCHED:
    js = T.code_only_js(left(p))
    for a, b in R.script_spans(js):
        for m in re.finditer(r'\.style(?:\.(\w+)|\[[^\]]+\])\s*(?:===|==|'
                             r'!==|!=)', js[a:b]):
            backs.append((T.rel(p), m.group(1) or '[computed]'))
colourish = [x for x in backs
             if x[1] and (x[1] == 'color' or 'olor' in x[1]
                          or 'ackground' in x[1] or 'order' in x[1])]
ok(not colourish,
   '%d style read-back(s) on these pages and NOT ONE reads a colour - they '
   'are all style.display. A write turned into var() and a comparison left '
   'on the old literal is this round fault class, and it does not occur'
   % len(backs), colourish[:4])


# ==========================================================================
head('6. THE BLACK - S-a SETTLED IT, SO THIS ROUND LEAVES IT')
# ==========================================================================
for p in TOUCHED:
    a = T.code_only(read(p + SUFFIX)).lower()
    b = T.code_only(left(p)).lower()
    if a.count('#000') != b.count('#000'):
        ok(False, '%s lost a #000' % T.rel(p),
           '%d -> %d' % (a.count('#000'), b.count('#000')))
        break
else:
    ok(True, 'every #000 survives on all %d pages' % len(TOUCHED))
ok('#000' in N.LEAVE_LIT,
   'the patcher names it on the leave list, with S-a reason')


# ==========================================================================
head('7. ONE LITERAL, TWO TIERS - THE PATCHER KEYS ON (literal, role)')
# ==========================================================================
src = read(os.path.join(ROOT, PATCHER))
ok("want = {(r['lit'], r['role'])" in src,
   'the want table is keyed on (literal, role)')
ok("want = {r['lit']:" not in src,
   '  and NOT on the literal alone - #6c757d is tier B as ink and tier C '
   'as a border, and one key collapses them')
ok(dist('#6c757d', N.TOKVAL['--alv-neutral']) <= 25
   and dist('#6c757d', N.TOKVAL['--alv-line']) > 25,
   '  proved on the numbers: %.1f units as ink, %.1f as a border'
   % (dist('#6c757d', N.TOKVAL['--alv-neutral']),
      dist('#6c757d', N.TOKVAL['--alv-line'])))


# ==========================================================================
head('8. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
imp = read(os.path.join(ROOT, 'alv_impact.py'))
ok('test_cssrules_outside.py' in imp and 'test_important_base.py' in imp,
   'alv_impact.COUNTERS carries the two census suites that were missing '
   'from it until B-4')
ok("'%s'" % ME in imp,
   'AND THIS SUITE ADDED ITSELF - sections 3 and 5 read every template in '
   'the tree, so a point round anywhere can break it, and the sweep rule '
   'is only as good as that hand-written list')

# ---- the six numbers this round moved, and it owns all six ------------
# This is the gate B-4's push failed on: it moved four of CR-1's census
# numbers and left them. The suite that owns the number is the right
# place to assert the round updated it.
cr = read(os.path.join(ROOT, 'test_cssrules_outside.py'))
for want in ('MARKUP_STYLE = 118', 'SCRIPT = 201', 'PAGES = 40',
             "'style-attr': 59", "'style-prop': 24", 'safe == 83'):
    ok(want in cr, '  CR-1 census now reads %s' % want)
ok("'canvas': 27" in cr and "'unknown': 91" in cr,
   '  and canvas 27 / unknown 91 did NOT move - 201 - 83 = 118 = 27 + 91, '
   'which is the arithmetic saying every refusal was honoured')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that tier C should convert at all. #adb5bd as')
print('  ink is 56 units from the nearest ink token and #dee2e6 as ink')
print('  is 134 - those are changes of appearance on nine list screens,')
print('  and the colour map says the render IS that decision. B-5b, with')
print('  renders, and his word.')
sys.exit(1 if failed else 0)
