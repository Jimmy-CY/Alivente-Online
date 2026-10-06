# -*- coding: utf-8 -*-
"""test_colour_neutrals.py - Section B round B-2, 6 Oct 2026.

758 literals on 93 templates became a var(), and UNLIKE B-1 THESE MOVED.
Between 9 and 25 RGB units, which is below what an eye reads as a
different colour and above nothing at all.

SO THE GATE IS BOUNDED, NOT AN EQUALITY, and section 2 is the round:
every substitution must move by EXACTLY the distance the map records, to
a tenth of a unit. "Within 25" would let a changed token slide 277
declarations somewhere nobody looked; "exactly 22.1" refuses.

SECTION 6 IS WHAT IT BOUGHT. Two of the four read measurably better -
the muted grey goes 4.69:1 to 5.53:1 on paper, and 4.69 clears the AA
floor for normal text by four hundredths on 229 uses of which a third
are set at 11px or 12px. The borders go the other way, 1.30 to 1.24, and
Demetri chose that on 6 Oct after looking at all four side by side:
--alv-line is already what every base-styled table draws with, so these
93 pages now AGREE with base instead of disagreeing.
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
import alv_tree
import alv_cssrules as R

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

from apply_colour_tokens import as_colour, role_of, root_values
from apply_colour_neutrals import (MAP, SUFFIX, MARK, EXPECT_CUTS,
                                   EXPECT_PAGES, CEILING, cuts_for, dist)

ME = 'test_colour_neutrals.py'
PATCHER = 'apply_colour_neutrals.py'
PS1 = 'Push-PendingChanges.ps1'
BOOTF = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

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
                 if os.path.exists(p + SUFFIX))

print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the nine substitutions')

VALS, ATS = root_values(now(BASEP))
ok(len(MAP) == 9, 'the map names %d (colour, role) pair(s)' % len(MAP))
for (col, role), (tok, want) in sorted(MAP.items(),
                                       key=lambda kv: -kv[1][1]):
    print('      %-9s %-5s -> var(%-20s) %-9s moves %5.1f'
          % (col, role, tok, VALS.get(tok, '?').strip(), want))

# ==========================================================================
head('2. THE GATE - exactly the move the map records, and no further')

off = []
for (col, role), (tok, want) in sorted(MAP.items()):
    got = as_colour(VALS.get(tok, '').strip()) if tok in VALS else None
    if got is None:
        off.append('%s is not a colour in base' % tok)
        continue
    d = dist(col, got)
    if abs(d - want) > 0.05:
        off.append('%s %s -> %s moves %.1f, the map says %.1f'
                   % (col, role, tok, d, want))
ok(not off, 'all %d move by exactly the recorded distance' % len(MAP),
   '\n'.join(off))
ok(max(w for _t, w in MAP.values()) <= CEILING,
   '  and the largest is %.1f, inside the %.1f ceiling'
   % (max(w for _t, w in MAP.values()), CEILING))

# THE CONTROL. A pair whose recorded move is wrong has to be caught by
# the same reading - not crash on it, and not quietly pass. This round's
# entire safety is that the number is checked rather than the family.
fake_want = 1.0
fake_d = dist('#6c757d', as_colour(VALS['--alv-ink-soft'].strip()))
ok(abs(fake_d - fake_want) > 0.05,
   '  the control: the same pair recorded as moving 1.0 is REJECTED, '
   'because it moves %.1f' % fake_d)
ok(dist('#6c757d', '#6c757d') == 0.0 and
   abs(dist('#000000', '#ffffff') - 441.7) < 0.1,
   '  and the measure itself is sane at both ends')

# ==========================================================================
head('3. the twelve standalone templates are untouched here too')

STAND = set(alv_tree.standalone())
BYNAME = {alv_tree.rel(q).replace(os.sep, '/'): q
          for q in alv_tree.templates()}
ok(len(STAND) == 12, '%d standalone template(s)' % len(STAND))
bad = [s for s in sorted(STAND) if os.path.exists(BYNAME[s] + SUFFIX)]
ok(not bad,
   '  none of them was rewritten - with no {% extends %} a var() there '
   'resolves to nothing', '\n'.join(bad))
left = []
for s in sorted(STAND):
    t = read(BYNAME[s])
    for (col, role) in MAP:
        if col in t.lower():
            left.append('%s still carries %s, as it should' % (s, col))
print('      %d of the twelve still carry one of the four literals, '
      'which is' % len({l.split()[0] for l in left}))
print('      the point: they cannot read a token, so they keep the '
      'colour.')

# ==========================================================================
head('4. every cut landed, and nothing was left behind')

tot = 0
rest = []
for p in TOUCHED:
    mine = cuts_for(alv_tree.code_only(was(p)))
    tot += len(mine)
    if cuts_for(alv_tree.code_only(now(p))):
        rest.append(alv_tree.rel(p))
ok(len(TOUCHED) == EXPECT_PAGES,
   '%d page(s) carry a %s backup' % (len(TOUCHED), SUFFIX))
ok(tot == EXPECT_CUTS,
   '  they held %d neutral literal(s) between them' % tot,
   'expected %d' % EXPECT_CUTS)
ok(not rest, '  and not one is left in the live files', '\n'.join(rest))

net = 0
for p in TOUCHED:
    a, b = was(p), now(p)
    for t in sorted({tok for tok, _w in MAP.values()}):
        net += b.count('var(%s)' % t) - a.count('var(%s)' % t)
ok(net == EXPECT_CUTS,
   '  %d new var() occurrence(s) appeared - one per cut, none spare' % net)

# B-1's bug, which cost a revert of 102 files and was caught by somebody
# else's render: style_spans has no comment awareness, and a CSS comment
# that MENTIONS a style tag is not a style tag.
loud = []
for p in TOUCHED:
    t = now(p)
    at = t.index(MARK)
    a = t.rfind('/*', 0, at)
    b = t.index('*/', at) + 2
    if a < 0 or alv_tree.code_only(t)[a:b].strip():
        loud.append(alv_tree.rel(p))
ok(not loud,
   '  and the note is a comment on all %d, not live CSS' % len(TOUCHED),
   '\n'.join(loud))

# ==========================================================================
head('5. the bounded diff - every cut moved, by exactly its own number')

moved = {}
wrong = []
for p in TOUCHED:
    for at, end, lit, prop, tok, sel in cuts_for(alv_tree.code_only(was(p))):
        col = as_colour(lit)
        want = MAP[(col, role_of(prop))][1]
        got = dist(col, as_colour(VALS[tok].strip()))
        if abs(got - want) > 0.05:
            wrong.append('%s %s %s -> %s moved %.1f not %.1f'
                         % (alv_tree.rel(p), sel, lit, tok, got, want))
        moved.setdefault(round(got, 1), 0)
        moved[round(got, 1)] += 1
ok(not wrong,
   'all %d cuts moved by the distance the map promised' % sum(moved.values()),
   '\n'.join(wrong[:6]))
ok(sum(moved.values()) == EXPECT_CUTS,
   '  every one of the %d was measured' % sum(moved.values()))
for d in sorted(moved, reverse=True):
    print('      %5.1f units  %4d cut(s)' % (d, moved[d]))
ok(max(moved) <= CEILING,
   '  and not one moved further than %.1f' % CEILING)

# AND NOT ONE PAGE CHANGED ITS SHAPE. The round rewrites values; the note
# it writes is a comment and cannot show up in either count.
def ndecl(t):
    n = 0
    for s_, e_ in R.style_spans(t):
        seen = set()
        for _sel, ba, bb, _ra, _rb in R.rule_spans(t, s_, e_):
            if (ba, bb) in seen:
                continue
            seen.add((ba, bb))
            body = re.sub(r'/\*.*?\*/', ' ', t[ba:bb], flags=re.S)
            n += len([d for d in body.split(';')
                      if ':' in d and '{' not in d and '}' not in d])
    return n


def nrule(t):
    n = 0
    for s_, e_ in R.style_spans(t):
        n += len({(ba, bb) for _s, ba, bb, _a, _b
                  in R.rule_spans(t, s_, e_)})
    return n


shifted = []
for p in TOUCHED:
    a, b = was(p), now(p)
    if (ndecl(a), nrule(a)) != (ndecl(b), nrule(b)):
        shifted.append('%s  decls %d->%d  rules %d->%d'
                       % (alv_tree.rel(p), ndecl(a), ndecl(b),
                          nrule(a), nrule(b)))
ok(not shifted,
   '  and not one page changed its rule or declaration count',
   '\n'.join(shifted[:6]))

# ==========================================================================
head('6. what it bought - contrast, measured, not asserted by eye')

PAPER = as_colour(VALS['--alv-paper'].strip())
SURF = as_colour(VALS['--alv-surface'].strip())
TEXT = [('#6c757d', 'INK', 'muted and small text', 229),
        ('#2c3e50', 'INK', 'headings and totals', 165),
        ('#495057', 'INK', 'labels and table heads', 107)]
LINE = [('#dee2e6', 'LINE', 'panel and card borders', 201)]

print('      %-9s %-24s %6s %6s   %6s %6s'
      % ('colour', 'what', 'paper', 'now', 'surf', 'now'))
better = 0
for col, role, what, n in TEXT + LINE:
    new = as_colour(VALS[MAP[(col, role)][0]].strip())
    a0, a1 = ratio(col, PAPER), ratio(new, PAPER)
    b0, b1 = ratio(col, SURF), ratio(new, SURF)
    print('      %-9s %-24s %6.2f %6.2f   %6.2f %6.2f  %s'
          % (col, what, a0, a1, b0, b1,
             'better' if a1 > a0 else 'fainter'))
    if a1 > a0:
        better += 1

soft = as_colour(VALS['--alv-ink-soft'].strip())
ok(ratio('#6c757d', PAPER) < 4.75,
   'the grey it replaced cleared the AA floor for normal text by %.2f'
   % (ratio('#6c757d', PAPER) - 4.5),
   '%.2f:1' % ratio('#6c757d', PAPER))
ok(ratio(soft, PAPER) >= 4.5 and ratio(soft, PAPER) > ratio('#6c757d', PAPER),
   '  and --alv-ink-soft clears it by %.2f, on 229 uses'
   % (ratio(soft, PAPER) - 4.5),
   '%.2f:1' % ratio(soft, PAPER))
ok(ratio(soft, SURF) >= 4.5,
   '  on the surface grey as well, which is where half of them sit',
   '%.2f:1' % ratio(soft, SURF))
ink = as_colour(VALS['--alv-ink'].strip())
ok(ratio(ink, PAPER) > ratio('#2c3e50', PAPER),
   '  and the heading ink goes %.2f to %.2f'
   % (ratio('#2c3e50', PAPER), ratio(ink, PAPER)))
ok(better == 2,
   '  %d of the four read better, which is what was claimed' % better)

# THE BORDERS GO THE OTHER WAY, AND THIS SAYS SO RATHER THAN HIDING IT.
line = as_colour(VALS['--alv-line'].strip())
ok(ratio(line, PAPER) < ratio('#dee2e6', PAPER),
   '  the 201 borders ARE fainter - %.2f down to %.2f - and that was the '
   'decision, not an oversight'
   % (ratio('#dee2e6', PAPER), ratio(line, PAPER)))
ok(abs(ratio('#dee2e6', PAPER) - ratio(line, PAPER)) < 0.1,
   '    by %.3f of a ratio point, on a line nobody reads'
   % abs(ratio('#dee2e6', PAPER) - ratio(line, PAPER)))

# A CONTROL, because a contrast formula that always says yes is not a
# check. Paper on paper must read 1.00 and ink on paper must not.
ok(abs(ratio(PAPER, PAPER) - 1.0) < 0.001 and ratio(ink, PAPER) > 10,
   '  the control: the formula reads 1.00 for a colour on itself and '
   '%.1f for the ink on paper' % ratio(ink, PAPER))

# ==========================================================================
head('7. the render - this time it is a comparison, not smoke')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

SIMPLE = re.compile(r'^\.[A-Za-z][-\w]*$')
PROP = {'INK': 'color', 'FILL': 'background-color', 'LINE': 'border-top-color'}

probe = {}
for p in TOUCHED:
    want = {}
    for at, end, lit, prop, tok, sel in cuts_for(alv_tree.code_only(was(p))):
        last = sel.split('&& ')[-1]
        if SIMPLE.match(last):
            want.setdefault(last[1:], set()).add(prop.lower())
    if want:
        probe[p] = want
BUSY = sorted(probe, key=lambda p: -sum(len(v) for v in probe[p].values()))[:10]

if sync_playwright is None:
    print('  --    the renders  (playwright missing)')
else:
    exe = '/opt/pw-browsers/chromium'
    bcss = css_of(alv_tree.code_only(now(BASEP)))
    boot = read(BOOTF) if os.path.exists(BOOTF) else ''
    KNOWN = {as_colour(VALS[t].strip()) for t, _w in MAP.values()}

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        def computed(page_css, width, want):
            divs = ''.join('<div class="%s" id="p_%d">x</div>'
                           % (k, i) for i, k in enumerate(sorted(want)))
            pg = br.new_page(viewport={'width': width, 'height': 900})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style>'
                '</head><body style="margin:0">%s</body></html>'
                % (boot, bcss, page_css, divs))
            out = pg.evaluate(
                '(spec) => { const o = {};'
                ' for (const [i, ps] of spec.entries()) {'
                '   const e = document.getElementById("p_" + i);'
                '   const s = getComputedStyle(e);'
                '   for (const p of ps) o[i + "|" + p] ='
                '     s.getPropertyValue(p); } return o; }',
                [sorted(want[k]) for k in sorted(want)])
            pg.close()
            return out

        def hexof(v):
            # SEARCH, DO NOT MATCH. A shorthand computes to
            # `1px solid rgb(222, 226, 230)` - the colour is not at the
            # start of the value, and a reader anchored at the start
            # reports every border in the round as unparseable. The
            # first build of this section did exactly that and called
            # 201 correct 8.8-unit moves a failure.
            m = re.search(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', v or '')
            return ('#%02x%02x%02x' % tuple(int(m.group(i))
                                            for i in (1, 2, 3))) if m else None

        far = []
        same = 0
        changed = 0
        shots = 0
        for p in BUSY:
            want = probe[p]
            a_css, b_css = css_of(was(p)), css_of(now(p))
            for w in (390, 1280):
                x = computed(a_css, w, want)
                y = computed(b_css, w, want)
                shots += 2
                for k in sorted(x):
                    if x[k] == y[k]:
                        same += 1
                        continue
                    changed += 1
                    ha, hb = hexof(x[k]), hexof(y[k])
                    if not ha or not hb:
                        far.append('%s %s  %r -> %r'
                                   % (alv_tree.rel(p), k, x[k], y[k]))
                    elif dist(ha, hb) > CEILING:
                        far.append('%s %s moved %.1f  %s -> %s'
                                   % (alv_tree.rel(p), k, dist(ha, hb),
                                      ha, hb))
                    elif hb not in KNOWN:
                        far.append('%s %s landed on %s, which is not one '
                                   'of this round tokens'
                                   % (alv_tree.rel(p), k, hb))
            print('      %-44s %2d class(es) painted at 390 and 1280'
                  % (alv_tree.rel(p), len(want)))
        br.close()

    ok(not far,
       'every painted value that changed moved at most %.1f and landed on '
       'a token of this round' % CEILING, '\n'.join(far[:6]))
    ok(changed > 0,
       '  %d painted value(s) DID change - this round is not a no-op, and '
       'a render that found nothing would be measuring nothing' % changed)
    print('      %d painted value(s) were unchanged; %d moved. Over %d '
          'painting(s).' % (same, changed, shots))

# ==========================================================================
head('8. registered')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok('.bak_coltok' in ROUNDS and
   ROUNDS.index('.bak_coltok') < ROUNDS.index(SUFFIX),
   '  and after B-1, which it builds on')
ok(ME in ps1, '%s is in the push suites' % ME)

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that 22.1 RGB units is invisible. Nothing in a')
print('  test can establish that - it is what Demetri said after looking')
print('  at all four side by side at phone and desktop width on 6 Oct.')
print('  What IS proved is that the move is 22.1 and not 40, that it is')
print('  the same 22.1 it was when he looked, and that it stops being')
print('  true the moment base changes.')
print()
print('  ALSO NOT PROVED: the rest of tier B. 343 uses remain inside 25')
print('  units of a token, in smaller families - that is B-2b. And 557')
print('  are a real colour change, which is tier C and needs a decision')
print('  each, not a bounded diff.')
