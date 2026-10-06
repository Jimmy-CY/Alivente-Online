# -*- coding: utf-8 -*-
"""test_colour_good_bad.py - Section B round B-3, 6 Oct 2026.

TIER C, AND THE FIRST ROUND THAT CANNOT SAY "NOTHING MOVED". B-1 asserted
equality. B-2 and B-2b asserted a bounded move - 25 RGB units, under what
an eye reads as a different colour. This one moves up to 88, and the only
honest defence of it is the one this suite measures: it makes the app
MORE readable, not less.

    #28a745 as text on paper      3.13:1  ->  5.12:1    --alv-good
    #28d168 as text on paper      2.02:1  ->  5.12:1
    #2ecc71 under white text      2.10:1  ->  5.12:1
    #16a34a as text on paper      3.30:1  ->  5.12:1
    #e74c3c as text on paper      3.82:1  ->  6.54:1    --alv-bad
    #dc3545 as text on paper      4.53:1  ->  6.54:1

Seven of the 23 pairs cross the AA line for normal text. Two go the other
way and both are named in the patcher rather than let through:
#0f5132 9.36 -> 8.57 and #721c24 11.01 -> 8.91, each still near twice
what AA asks.

SECTION 4 IS THE ONE A (colour, role) MAP CANNOT DO. Ten of the greens
and reds in this round are HOVER STATES of the solids, and distance alone
sends #218838 to --alv-good - the same token as the button it is the
hover for. The hover would then do nothing, or go the wrong way, because
--alv-good is DARKER than Bootstrap's hover green. So the map sends every
hover-dark to the family's -ink token, and this section pairs all 21
rest/hover pairs in the tree and requires each one still to be darker on
hover AFTER the substitution. Measured from the files, before and after,
not assumed.

SECTION 5 IS WHAT WAS LEFT OUT ON PURPOSE. A hue test sweeps up the
recipe browns, a pink, a burnt orange and Bootstrap's teal. None of them
is this family, all of them are still in the tree, and the suite asserts
they were not touched - because a scope that is only in a comment is a
scope nobody checks.

Run it against the REVERTED tree and it must FAIL, not crash.
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
import collections
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree                                          # noqa: E402
import alv_cssrules as R                                 # noqa: E402

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:                                        # pragma: no cover
    ROUNDS, as_left_by = [], None

from apply_colour_tokens import as_colour, role_of, root_values  # noqa: E402
from apply_colour_good_bad import (DIPS, EXPECT_CUTS, EXPECT_PAGES, MAP,
                                   MARK, SUFFIX, base_of, cuts_for, dist,
                                   states)                # noqa: E402

ME = 'test_colour_good_bad.py'
PATCHER = 'apply_colour_good_bad.py'
PS1 = 'Push-PendingChanges.ps1'
BOOTF = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

AA = 4.5
FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def lum(h):
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


BASEP = alv_tree.path_of('base.html')
TOUCHED = sorted(p for p in alv_tree.templates()
                 if os.path.exists(p + SUFFIX)
                 and alv_tree.rel(p) != 'base.html')

print(__doc__.strip().splitlines()[0])

VALS, ATS = root_values(now(BASEP))
PAPER = as_colour(VALS['--alv-paper'].strip())
WHITE = '#ffffff'

# ==========================================================================
head('1. the map: two families, three shades each')

ok(len(MAP) == 23, 'the map names %d (colour, role) pair(s)' % len(MAP),
   len(MAP))

bytok = collections.defaultdict(list)
for (col, role), (tok, move) in MAP.items():
    bytok[tok].append((col, role, move))
for tok in sorted(bytok):
    ok(tok in VALS, '  %-18s %-9s %d pair(s)'
       % (tok, VALS.get(tok, '?').strip(), len(bytok[tok])))

ok(set(bytok) == {'--alv-good', '--alv-good-ink', '--alv-good-soft',
                  '--alv-bad', '--alv-bad-ink'},
   'and it reaches five tokens, all of them in the good and bad families',
   sorted(bytok))
ok(not any(t.startswith('--alv-neutral') or '-tag-' in t for t in bytok),
   '  not one of them is a named family reached by distance',
   'the map method: --alv-neutral and the five tag families are reached '
   'by meaning, never because they happen to be nearest')

bad = []
for (col, role), (tok, want) in sorted(MAP.items()):
    d = dist(col, as_colour(VALS[tok].strip()))
    if abs(d - want) > 0.05:
        bad.append('%s %s -> %s moves %.1f, the map says %.1f'
                   % (col, role, tok, d, want))
ok(not bad, 'every move is exactly the distance the map records',
   '\n'.join(bad))
ok(max(w for _t, w in MAP.values()) > 25.0,
   'and the largest is %.1f - OVER the tier B ceiling, which is what '
   'makes this tier C' % max(w for _t, w in MAP.values()))

# ==========================================================================
head('2. the census: 250 cuts on 43 pages, and the literals are gone')

ok(len(TOUCHED) == EXPECT_PAGES,
   '%d page(s) carry a %s backup' % (len(TOUCHED), SUFFIX), len(TOUCHED))

before = sum(len(cuts_for(alv_tree.code_only(was(p)))) for p in TOUCHED)
ok(before == EXPECT_CUTS,
   'CONTROL: those pages held %d literal(s) from the two families before'
   % before, before)

after = sum(len(cuts_for(alv_tree.code_only(now(p)))) for p in TOUCHED)
ok(after == 0, 'and none of them now', after)

noted = [p for p in TOUCHED if MARK not in now(p)]
ok(not noted, 'every one of the %d says what it took and why'
   % len(TOUCHED), [alv_tree.rel(p) for p in noted[:5]])

# AND NOWHERE ELSE IN THE TREE EITHER - the standalone twelve excepted,
# because base cannot reach them and a var() there resolves to nothing.
stand = set(alv_tree.standalone())
stray = []
for p in alv_tree.templates():
    rel = alv_tree.rel(p).replace(os.sep, '/')
    if rel in stand or rel == 'base.html':
        continue
    n = len(cuts_for(alv_tree.code_only(now(p))))
    if n:
        stray.append('%s %d' % (rel, n))
ok(not stray, 'and not one page outside the twelve standalone templates '
   'still carries one', stray[:6])

# ==========================================================================
head('3. contrast: seven pairs cross AA, and nothing ends below it')


def pair_ratio(col, role, tok):
    """How the colour is actually read, by role.

    A LINE is seen, not read, so it is not measured. An INK sits on
    paper. A FILL carries white text - except a -soft, which is a wash,
    and what sits on a wash is its own family's ink.
    """
    new = as_colour(VALS[tok].strip())
    if role == 'LINE':
        return None, None
    if tok.endswith('-soft'):
        ink = as_colour(VALS[tok.replace('-soft', '-ink')].strip())
        return ratio(ink, col), ratio(ink, new)
    if role == 'INK':
        return ratio(col, PAPER), ratio(new, PAPER)
    return ratio(WHITE, col), ratio(WHITE, new)


crossed, under, dipped = [], [], []
for (col, role), (tok, _w) in sorted(MAP.items()):
    b, a = pair_ratio(col, role, tok)
    if b is None:
        continue
    if a < AA:
        under.append('%s %s -> %s ends at %.2f:1' % (col, role, tok, a))
    if b < AA <= a:
        crossed.append('%s %s -> %s  %.2f:1 -> %.2f:1'
                       % (col, role, tok, b, a))
    if a < b - 0.01:
        dipped.append((col, role, tok, b, a))

ok(not under, 'not one pair ends under %.1f:1' % AA, '\n'.join(under))
ok(len(crossed) == 7, '%d pair(s) move from under AA to over it'
   % len(crossed), '\n'.join(crossed))
for line in crossed:
    print('        %s' % line)

ok(len(dipped) == len(DIPS),
   'and exactly %d lose anything at all, which is what the patcher '
   'writes down' % len(DIPS),
   ['%s %s -> %s %.2f -> %.2f' % d for d in dipped])
for col, role, tok, b, a in dipped:
    ok((col, role) in DIPS and DIPS[(col, role)] == tok,
       '  %s %s -> %s  %.2f:1 -> %.2f:1, named in DIPS'
       % (col, role, tok, b, a))
    ok(a >= AA * 1.5, '    and still at %.2f:1, well over AA' % a, a)

# THE GREEN WAS THE DEFECT, and saying so in one assertion rather than
# leaving it in a docstring.
ok(ratio('#28a745', PAPER) < AA,
   'CONTROL: Bootstrap success green really did fail AA on paper - '
   '%.2f:1' % ratio('#28a745', PAPER))
ok(ratio(as_colour(VALS['--alv-good'].strip()), PAPER) >= AA,
   '  and --alv-good clears it at %.2f:1'
   % ratio(as_colour(VALS['--alv-good'].strip()), PAPER))

# ==========================================================================
head('4. the hovers: 21 pairs, still darker after the move')


def resolved(col, prop):
    role = role_of(prop)
    hit = MAP.get((col, role)) if role else None
    return as_colour(VALS[hit[0]].strip()) if hit else col


pairs, broke, flat = 0, [], []
for p in alv_tree.templates():
    rel = alv_tree.rel(p).replace(os.sep, '/')
    if rel in stand:
        continue
    src = alv_tree.code_only(was(p) if os.path.exists(p + SUFFIX) else now(p))
    rest, hover = states(src)
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
            pairs += 1
            r0, h0 = lum(rcol), lum(hcol)
            r1, h1 = lum(resolved(rcol, prop)), lum(resolved(hcol, prop))
            if h0 < r0 and not h1 < r1:
                broke.append('%s %s %s: %s/%s' % (rel, key, prop, rcol, hcol))
            if h0 != r0 and h1 == r1:
                flat.append('%s %s %s: %s and %s became the same colour'
                            % (rel, key, prop, rcol, hcol))

ok(pairs == 21, '%d rest/hover pair(s) in the two families' % pairs, pairs)
ok(not broke, 'every one that was darker on hover still is',
   '\n'.join(broke))
ok(not flat, 'and not one pair was flattened into a single colour',
   '\n'.join(flat))

# THE TRAP, STATED AS A MEASUREMENT. If #218838 had gone to --alv-good
# like its rest state, this is the number that would have broken.
g, gi = (as_colour(VALS['--alv-good'].strip()),
         as_colour(VALS['--alv-good-ink'].strip()))
ok(lum('#218838') < lum('#28a745'),
   'CONTROL: Bootstrap hover green really is darker than its rest')
ok(lum(gi) < lum(g),
   '  and --alv-good-ink is darker than --alv-good, so the pair survives')
ok(lum(g) < lum('#218838'),
   '  while --alv-good is darker than the hover it replaces - which is '
   'why sending both to --alv-good would have INVERTED the button')

# ==========================================================================
head('5. scope: what a hue test would have swept up, and did not')

# A comment is not a scope. These are named, and the assertion is that
# they are still in the tree with their literals intact.
OUT = {
    '#2c1810': 'a recipe brown',
    '#5c3a2a': 'a recipe brown',
    '#5d4037': 'a recipe brown',
    '#e83e8c': 'pink, not a red',
    '#c2410c': 'a burnt orange - the warn round owns it',
    '#20c997': "Bootstrap teal - nearer the accent",
}
LIVE = {}
for p in alv_tree.templates():
    rel = alv_tree.rel(p).replace(os.sep, '/')
    if rel in stand or rel == 'base.html':
        continue
    code = alv_tree.code_only(now(p))
    for col in OUT:
        LIVE[col] = LIVE.get(col, 0) + len(re.findall(re.escape(col), code,
                                                      re.I))
for col, why in sorted(OUT.items()):
    ok(LIVE.get(col, 0) > 0, '%s is untouched - %s (%d use(s) left)'
       % (col, why, LIVE.get(col, 0)), LIVE.get(col, 0))
    ok(not any(c == col for c, _r in MAP),
       '  and it is not in the map')

# ==========================================================================
head('6. the render - computed longhands, both widths')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

SIMPLE = re.compile(r'^\.[A-Za-z][-\w]*$')

probe = {}
for p in TOUCHED:
    want = set()
    for at, end, lit, prop, tok, sel in cuts_for(alv_tree.code_only(was(p))):
        last = sel.split('&& ')[-1]
        if SIMPLE.match(last):
            want.add(last[1:])
    if want:
        probe[p] = sorted(want)
BUSY = sorted(probe, key=lambda p: -len(probe[p]))[:8]

if sync_playwright is None:
    print('  --    the renders  (playwright missing)')
elif not BUSY:
    print('  --    the renders  (no simple selectors to probe)')
else:
    exe = '/opt/pw-browsers/chromium'
    bcss = css_of(alv_tree.code_only(now(BASEP)))
    boot = read(BOOTF) if os.path.exists(BOOTF) else ''

    # ASK FOR THE LONGHAND, NOT THE SHORTHAND. B-2b's lesson: the
    # computed `background` shorthand begins with the transparent
    # background-COLOR, so a reader taking the first colour out of it
    # reports every gradient as having turned black.
    PROBES = ['color', 'background-color', 'background-image',
              'border-top-color', 'border-right-color',
              'border-bottom-color', 'border-left-color', 'outline-color']
    RGB = re.compile(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([0-9.]+))?\)')

    def colours(v):
        out = []
        for m in RGB.finditer(v or ''):
            if m.group(4) is not None and float(m.group(4)) < 0.999:
                continue
            out.append('#%02x%02x%02x'
                       % tuple(int(m.group(i)) for i in (1, 2, 3)))
        return out

    FROM = {c for c, _r in MAP}
    TO = {as_colour(VALS[t].strip()) for t, _w in MAP.values()}

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        def computed(page_css, width, klasses):
            divs = ''.join('<div class="%s" id="p_%d">x</div>'
                           % (k, i) for i, k in enumerate(klasses))
            pg = br.new_page(viewport={'width': width, 'height': 900})
            pg.route('**://*/**', lambda r: r.abort())
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style>'
                '</head><body style="margin:0">%s</body></html>'
                % (boot, bcss, page_css, divs))
            out = pg.evaluate(
                '(spec) => { const o = {};'
                ' for (let i = 0; i < spec.n; i++) {'
                '   const e = document.getElementById("p_" + i);'
                '   const s = getComputedStyle(e);'
                '   for (const p of spec.props) o[i + "|" + p] ='
                '     s.getPropertyValue(p); } return o; }',
                {'n': len(klasses), 'props': PROBES})
            pg.close()
            return out

        for width in (1280, 390):
            left, moved, wrong = 0, 0, []
            for p in BUSY:
                ks = probe[p]
                b = computed(css_of(alv_tree.code_only(was(p))), width, ks)
                a = computed(css_of(alv_tree.code_only(now(p))), width, ks)
                for k in b:
                    cb, ca = colours(b[k]), colours(a[k])
                    if len(cb) != len(ca):
                        wrong.append('%s %s: %d colour(s) became %d'
                                     % (alv_tree.rel(p), k, len(cb),
                                        len(ca)))
                        continue
                    for x, y in zip(cb, ca):
                        if x == y:
                            continue
                        moved += 1
                        if x not in FROM or y not in TO:
                            wrong.append('%s %s: %s became %s, which is not '
                                         'a move this map makes'
                                         % (alv_tree.rel(p), k, x, y))
                    left += sum(1 for x in ca if x in FROM)
            ok(not wrong, 'at %d: every rendered change is one the map '
               'makes - %d declaration(s) moved' % (width, moved),
               '\n'.join(wrong[:6]))
            ok(left == 0, '  and not one of the old literals is left '
               'rendering at %d' % width, left)
            ok(moved > 0, '  CONTROL: something really did change at %d'
               % width, moved)
        br.close()

# ==========================================================================
head('7. scope, registered, on the gate')

for p in TOUCHED:
    a, b = was(p), now(p)
    if len(b) <= len(a):
        ok(False, '%s did not grow - the note is missing'
           % alv_tree.rel(p))
        break
else:
    ok(True, 'all %d pages grew by their note and nothing else'
       % len(TOUCHED))

bal = [alv_tree.rel(p) for p in TOUCHED
       if now(p).count('{%') != was(p).count('{%')
       or now(p).count('%}') != was(p).count('%}')]
ok(not bal, 'every Django tag survived on all %d' % len(TOUCHED), bal[:5])

ok(now(BASEP) == was(BASEP) if os.path.exists(BASEP + SUFFIX) else True,
   'base.html is not in this round - it is where the tokens are defined')

rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(rounds.index("'.bak_rooturl'") < rounds.index("'%s'" % SUFFIX),
   '  and after .bak_rooturl, the round before it')
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  WHAT IS LEFT OF TIER C: the amber, the greys, the black, the')
print('  blues and the one-page browns - roughly 295 uses. The amber is')
print('  the one that cannot borrow any of this: #ffc107 is paired with')
print('  DARK text today and reads 7.95:1, while --alv-warn under the')
print('  same ink is 2.41:1. A straight swap would break it. base')
print('  already writes the answer - .alv-pill-attn is warn-soft under')
print('  warn ink at 4.88:1 - so B-4 is a change of STRUCTURE per use,')
print('  not a substitution, and it needs its own renders.')
