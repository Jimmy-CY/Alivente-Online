# -*- coding: utf-8 -*-
"""test_amber.py - Section B round B-4, 7 Oct 2026.

The amber, at the scope decision 9 set: CSS, inline style= attributes
and <script>.

HE TOOK THIS ONE AGAINST MY ADVICE, KNOWING THE COST. The Warning chip
reads 10.24:1 today and 4.88:1 after. I recommended fixing only what
fails AA and leaving the bright pills; he chose all seven, consistency
over contrast, after seeing both numbers. Section 4 records it so the
quieter chip is never re-raised as a regression.

WHAT THE MEASUREMENT OVERTURNED FIRST. I told him the borders were a
plain swap. #ffc107 to --alv-warn-line is 153 units and to --alv-warn is
148 - the same size as the fill change the colour map called the biggest
in the programme. Only 6 of 62 CSS uses sit within 25 units of any warn
token, so there was never an invisible half to land first.

AND THE PILLS ARE RESTRUCTURED, NOT SUBSTITUTED. .alv-pill-attn is a
COLOUR modifier on .alv-pill, which carries 12px type, 3px/10px padding
and a 999px radius. .anchor-pill is 10px, 1px/6px, 8px. Adding the class
would have resized seven pills nobody asked to resize, so the round
writes the three colour declarations into each page's own rule and
leaves every shape alone. Section 3 proves the shapes did not move.

SECTION 7 IS THE ROUND KEEPING ITS WORD. Ten amber literals inside
<script> are REFUSED, because js_colour_context cannot classify them and
a round refuses what it cannot classify rather than guessing.

SECTION 8 IS THE ONE I NEARLY GOT WRONG. test_fsr_palette says in as
many words that fsr_details keeps #ecd9a8 - "the Notify round's
page-local warn tint, DECIDED last night with a single asker". B-4
converted it, and that suite caught it. It is 10 units from
--alv-warn-line, so the conversion would have been invisible and
arguably right, which is exactly why it needed asking. A round that
quietly reverses another round's recorded decision is worse than one
that leaves a literal behind.
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

SUFFIX = '.bak_amber'
ME = 'test_amber.py'
PATCHER = 'apply_amber.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'B-4, 7 Oct 2026'

EXPECT_PAGES = 23
EXPECT_REFUSED = 10
WARN, SOFT, INK, LINE = ('--alv-warn', '--alv-warn-soft',
                         '--alv-warn-ink', '--alv-warn-line')

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
import apply_amber as B                                    # noqa: E402
import alv_rounds as RD                                    # noqa: E402

TOUCHED = sorted(p for p in T.templates() if os.path.isfile(p + SUFFIX))


def css(text):
    c = T.code_only(text)
    return '\n'.join(c[a:b] for a, b in R.style_spans(c))


def rule(path, tail, text=None):
    code = T.code_only(read(path) if text is None else text)
    for a, b in R.style_spans(code):
        for sel, ba, bb, _r, _s in R.rule_spans(code, a, b):
            if sel.split(' && ')[-1].strip() == tail:
                return R.norm(code[ba:bb])
    return None


# ==========================================================================
head('1. SCOPE')
# ==========================================================================
ok(len(TOUCHED) == EXPECT_PAGES, '%d pages' % EXPECT_PAGES,
   [T.rel(p) for p in TOUCHED])
stand = set(T.standalone())
ok(not [p for p in TOUCHED if T.rel(p) in stand],
   'and not one standalone template - they have no :root to read')
ok(not os.path.isfile(T.path_of('base.html') + SUFFIX),
   'base.html was not touched - this round defines no token')


# ==========================================================================
head('2. NO AMBER LITERAL SURVIVES WHERE IT WAS CONVERTED')
# ==========================================================================
stray = []
for p in TOUCHED:
    code = T.code_only(read(p))
    js = T.code_only_js(read(p))
    inscript = R.script_spans(js)
    keep = []
    for (pg, tail), _why in B.LEAVE_RULES.items():
        if pg != T.rel(p):
            continue
        for a, b in R.style_spans(code):
            for sel, ba, bb, _r, _s in R.rule_spans(code, a, b):
                if sel.split(' && ')[-1].strip() == tail:
                    keep.append((ba, bb))
    for m in re.finditer(r'#ffc107', code, re.I):
        if any(a <= m.start() < b for a, b in inscript):
            continue
        if any(a <= m.start() < b for a, b in keep):
            continue
        stray.append('%s at %d' % (T.rel(p), m.start()))
ok(not stray,
   'not one #ffc107 is left in CSS or in a style= attribute on any of the '
   '%d pages' % len(TOUCHED), stray[:6])
used = set()
for p in TOUCHED:
    for tok in (WARN, SOFT, INK, LINE):
        if 'var(%s)' % tok in read(p):
            used.add(tok)
ok(used == {WARN, SOFT, INK, LINE},
   'and all four warn tokens are now in use across the tree', sorted(used))


# ==========================================================================
head('3. THE PILLS - RESTRUCTURED, AND THEIR SHAPE UNTOUCHED')
# ==========================================================================
PILLS = (('home.html', '.status-warning'),
         ('notifications.html', '.status-warning'),
         ('finance_expense_add.html', '.anchor-pill'),
         ('finance_expense_edit.html', '.anchor-pill'),
         ('my_profile.html', '.coming-soon-badge'),
         ('act_expense.html', '.an-badge.ytd'))
for pg, tail in PILLS:
    path = T.path_of(pg)
    if not path:
        skip(pg, 'not in this tree')
        continue
    now = rule(path, tail) or ''
    was = rule(path, tail, read(path + SUFFIX)) or ''
    ok('var(%s)' % SOFT in now, '%-26s %s has the soft fill' % (pg, tail), now)
    ok('var(%s)' % WARN in now, '  and the warn ink')
    ok('var(%s)' % LINE in now, '  and a warn-line border')
    # THE SHAPE DID NOT MOVE. This is the claim that .alv-pill-attn as a
    # class would have broken.
    for prop in ('font-size', 'padding', 'border-radius'):
        a = re.search(prop + r'\s*:\s*([^;]+)', was)
        b = re.search(prop + r'\s*:\s*([^;]+)', now)
        if a or b:
            ok(bool(a) == bool(b) and (not a or
                                       R.norm(a.group(1)) == R.norm(b.group(1))),
               '  %s is exactly as it was' % prop,
               '%s -> %s' % (a and a.group(1), b and b.group(1)))


# ==========================================================================
head('4. THE INK - AND WHAT HE CHOSE KNOWING THE COST')
# ==========================================================================
# 9 uses were below AA and now clear it. The patcher refuses the round if
# any use that passes today would drop, so this asserts the direction.
FIXED = (('map_ingredients_nutrition.html', '.undo-toast .toast-undo-btn'),
         ('home.html', '.ins-tag--amber'),
         ('my_profile.html', '.coming-soon-badge'))
for pg, tail in FIXED:
    path = T.path_of(pg)
    if not path:
        skip(pg, 'not in this tree')
        continue
    now = rule(path, tail) or ''
    ok('var(--alv-warn' in now,
       '%-30s %s now reads a warn token' % (pg, tail), now[:90])
ok(B.contrast('#ffc107', '#ffffff') < 4.5,
   'amber text on paper was %.2f:1 - below AA'
   % B.contrast('#ffc107', '#ffffff'))
ok(B.contrast(B.TOKVAL[INK], '#ffffff') >= 4.5,
   '  and warn-ink on paper is %.2f:1 - above it'
   % B.contrast(B.TOKVAL[INK], '#ffffff'))
ok(B.contrast(B.TOKVAL[SOFT], B.TOKVAL[WARN]) >= 4.5,
   'the pill treatment reads %.2f:1 - it passes AA'
   % B.contrast(B.TOKVAL[SOFT], B.TOKVAL[WARN]))
ok(B.contrast('#ffc107', '#15201f') > B.contrast(B.TOKVAL[SOFT],
                                                 B.TOKVAL[WARN]),
   'AND IT IS LOWER THAN WHAT IT REPLACED (%.2f -> %.2f). He chose '
   'consistency over contrast after seeing both numbers. The Warning chip '
   'is MEANT to be quieter now.'
   % (B.contrast('#ffc107', '#15201f'),
      B.contrast(B.TOKVAL[SOFT], B.TOKVAL[WARN])))


# ==========================================================================
head('5. A HOVER STAYS DARKER THAN ITS REST STATE  [B-3]')
# ==========================================================================
inverted = []
pairs = 0
for p in TOUCHED:
    code = T.code_only(read(p))
    vals = {}
    for a, b in R.style_spans(code):
        for sel, ba, bb, _r, _s in R.rule_spans(code, a, b):
            for prop in ('background', 'background-color', 'color'):
                d = R.decl_span(code, ba, bb, prop)
                if d is None:
                    continue
                v = R.norm(code[d[0]:d[1]].partition(':')[2]).rstrip(';')
                m = re.search(r'var\((--[\w-]+)\)', v)
                hexv = B.TOKVAL.get(m.group(1)) if m else None
                if hexv is None:
                    m2 = re.search(r'#[0-9a-fA-F]{3,8}(?![\w-])', v)
                    hexv = m2.group(0) if m2 else None
                if hexv:
                    vals[(sel, prop)] = hexv
    for (sel, prop), v in vals.items():
        if ':hover' not in sel:
            continue
        rest = vals.get((sel.replace(':hover', ''), prop))
        if not rest:
            continue
        pairs += 1
        if B.lum(v) > B.lum(rest) + 1e-9:
            inverted.append('%s %s %s  rest %s -> hover %s'
                            % (T.rel(p), sel, prop, rest, v))
ok(not inverted,
   '%d rest/hover pair(s) on these pages, and every one is still darker '
   'under the pointer' % pairs, inverted[:4])
ok(pairs >= 4, '  and there are pairs to check', pairs)


# ==========================================================================
head('6. THE LEAVE LIST - EVERY ONE UNTOUCHED, WITH ITS REASON')
# ==========================================================================
# B-7, 9 Oct 2026 - THIS ASKS ABOUT B-4, NOT ABOUT TODAY.
#
# It used to compare the tree NOW against a "before" that
# read the live file for every page B-4 had not touched.
# That figure falls whenever a later round legitimately
# converts one of these literals on such a page, so RC-2
# added a dict of what it had taken and B-7 needed another
# - and the number each had to contain was not what the
# round took but what it took on pages B-4 happened to
# touch, which nothing can derive. Two rounds, two wrong
# answers.
#
# What this section means is that B-4 LEFT THESE ALONE.
# That is a fact about B-4 and permanently true, so it is
# asserted against B-4's own before and after, and no
# later round has to compensate for it ever again.
for lit, why in sorted(B.LEAVE.items()):
    b4_before = b4_after = 0
    for p in T.templates():
        after = T.code_only(RD.as_left_by(p, SUFFIX, read)).lower()
        before = (T.code_only(read(p + SUFFIX)).lower()
                  if p in TOUCHED else after)
        b4_after += after.count(lit)
        b4_before += before.count(lit)
    ok(b4_before == b4_after,
       '%-9s B-4 left it alone - %s' % (lit, why[:48]),
       '%d after B-4, %d before it' % (b4_after, b4_before))

for (pg, tail), why in B.LEAVE_RULES.items():
    path = T.path_of(pg)
    now = rule(path, tail) or ''
    ok('#ffc107' in now.lower(),
       '%s %s keeps its bright amber - %s' % (pg, tail, why[:46]), now)


# ==========================================================================
head('7. THE TEN THE ROUND REFUSED')
# ==========================================================================
refused = 0
for p in TOUCHED + [q for q in T.templates() if q not in TOUCHED]:
    js = T.code_only_js(read(p))
    for a, b in R.script_spans(js):
        for s, _e, lit in R.colour_spans(js, a, b):
            if lit.lower() != '#ffc107' and lit.lower() != '#eda100':
                continue
            if R.js_colour_context(js, s, a) not in R.VAR_SAFE:
                refused += 1
ok(refused >= EXPECT_REFUSED,
   'at least %d amber literal(s) inside <script> are still literal, '
   'because js_colour_context cannot classify them' % EXPECT_REFUSED,
   refused)
ok('canvas' not in R.VAR_SAFE,
   '  and canvas is still not var-safe, which is why that matters')


# ==========================================================================
head('8. ANOTHER ROUND DECIDED #ecd9a8, AND B-4 DOES NOT OVERTURN IT')
# ==========================================================================
fsr = T.path_of('fsr_details.html')
if fsr:
    ok('#ecd9a8' in T.code_only(read(fsr)),
       "fsr_details.html still spells #ecd9a8 by hand - the Notify round's "
       'page-local warn tint, decided deliberately')
    ok(not os.path.isfile(fsr + SUFFIX),
       '  and B-4 did not touch that page at all')
    ok('#ecd9a8' in B.LEAVE,
       '  the patcher names it on the leave list, with the reason')
else:
    skip('the fsr_details check', 'the page is not in this tree')
ok(B.dist('#ecd9a8', B.TOKVAL[LINE]) <= 25 if hasattr(B, 'dist') else True,
   '  it is within 25 units of --alv-warn-line, so folding it in would be '
   'INVISIBLE - which is exactly why it needed asking rather than doing')


# ==========================================================================
head('9. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the dashboard chart segment, its legend')
print('  swatch and the Gantt bar belong outside the warn family. They')
print('  are left alone because they are SERIES colours and the house')
print('  has no chart palette to send them to - mapping them to a warn')
print('  token would say this is a warning about a band that is merely')
print('  one of several. That is a decision of its own and nobody has')
print('  taken it yet.')
sys.exit(1 if failed else 0)
