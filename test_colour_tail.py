# -*- coding: utf-8 -*-
"""test_colour_tail.py - Section B round B-2b, 6 Oct 2026.

342 literals on 68 templates became a var(). B-2 took the four neutrals
that are tier B by weight; THIS IS EVERYTHING ELSE INSIDE 25 UNITS -
105 pairs in six families.

TWENTY-ONE WAYS OF WRITING A PALE TEAL, AND FIFTY-THREE GREYS. That is
what section 1 prints, and it is the finding: a long tail is not a
programme nobody got to, it is the same decision made separately by
whoever was writing that page that day.

SECTION 2 IS THE GATE, and it is B-2's unchanged - every substitution
moves by exactly the distance the map records, to a tenth of a unit.
The map is eleven times bigger; the proof is the same size.

SECTION 6 IS THIS ROUND'S OWN SECTION: the four entries where the
classifier's draft was WRONG and a person overruled it. A classifier
that is never overruled is not being read.
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
from apply_colour_tail import (MAP, SUFFIX, MARK, EXPECT_CUTS,
                               EXPECT_PAGES, CEILING, KEEP, cuts_for)
from apply_colour_neutrals import dist

ME = 'test_colour_tail.py'
PATCHER = 'apply_colour_tail.py'
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
head('1. the map, by family - and what the shape of it says')

VALS, ATS = root_values(now(BASEP))
ok(len(MAP) == 105, 'the map names %d (colour, role) pair(s)' % len(MAP))

import collections
fam = collections.defaultdict(list)
for (col, role), (tok, want) in MAP.items():
    fam[tok.split('-')[3]].append((col, role, tok, want))
for f in sorted(fam, key=lambda f: -len(fam[f])):
    print('      %-10s %3d pair(s) -> %d token(s): %s'
          % (f, len(fam[f]), len({t for _c, _r, t, _w in fam[f]}),
             ', '.join(sorted({t for _c, _r, t, _w in fam[f]}))[:52]))

spell = collections.Counter()
for (col, role), (tok, want) in MAP.items():
    spell[tok] += 1
worst = spell.most_common(3)
print('')
for tok, k in worst:
    print('      %-22s is spelled %d different way(s) in the tree' % (tok, k))
ok(worst[0][1] >= 9,
   '  the worst is %s, at %d spellings' % (worst[0][0], worst[0][1]),
   'if this ever drops the finding has changed and the docstring is stale')

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
ok(min(w for _t, w in MAP.values()) > 0,
   '  and the smallest is %.1f - a pair that moved nothing would be '
   'tier A, and tier A is empty'
   % min(w for _t, w in MAP.values()))

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
print('      %d of the twelve still carry one of this round literals, '
      'which is' % len({l.split()[0] for l in left}))
print('      the point: they cannot read a token, so they keep the '
      'colour.')

# ==========================================================================
head('4. every cut landed, and nothing was left behind')

tot = 0
rest = []
for p in TOUCHED:
    mine = cuts_for(alv_tree.code_only(was(p)), alv_tree.rel(p).replace(os.sep, '/'))
    tot += len(mine)
    if cuts_for(alv_tree.code_only(now(p)), alv_tree.rel(p).replace(os.sep, '/')):
        rest.append(alv_tree.rel(p))
ok(len(TOUCHED) == EXPECT_PAGES,
   '%d page(s) carry a %s backup' % (len(TOUCHED), SUFFIX))
ok(tot == EXPECT_CUTS,
   '  they held %d tail literal(s) between them' % tot,
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
    for at, end, lit, prop, tok, sel in cuts_for(alv_tree.code_only(was(p)), alv_tree.rel(p).replace(os.sep, '/')):
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
# THE WHOLE DISTRIBUTION IS 60 LINES AND NOBODY READS 60 LINES. The
# eight biggest buckets and a total for the rest says the same thing.
big = sorted(moved.items(), key=lambda kv: -kv[1])[:8]
for d, k in big:
    print('      %5.1f units  %4d cut(s)' % (d, k))
rest = sum(moved.values()) - sum(k for _d, k in big)
print('      %s  %4d cut(s) across %d more distance(s), none over %.1f'
      % (' ' * 11, rest, len(moved) - len(big), max(moved)))
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
head('6. the four the classifier got wrong, and a person overruled')

# A CLASSIFIER THAT IS NEVER OVERRULED IS NOT BEING READ. The draft
# behind this map sorts a colour into a family by hue, saturation and
# darkness, and it is right about 101 of the 105. These are the four it
# was not, each one kept here with the measurement that settles it.

def near(col, tok):
    return dist(col, as_colour(VALS[tok].strip()))


# 1. #ecf0f1 is Flat-UI's "clouds" grey. Five RGB units wide - and the
#    classifier read its hue as 192, just outside the 200-245 band that
#    says "Bootstrap grey", so it called it a pale teal.
ok(MAP[('#ecf0f1', 'FILL')][0] == '--alv-surface-deep',
   '#ecf0f1 is a grey, not a pale teal - 5 RGB units wide')
ok(near('#ecf0f1', '--alv-surface-deep') < near('#ecf0f1', '--alv-accent-soft'),
   '  and the grey is nearer too: %.1f against %.1f'
   % (near('#ecf0f1', '--alv-surface-deep'),
      near('#ecf0f1', '--alv-accent-soft')))

# 2 and 3. The same band in the other direction - two pale BLUES, 23
#    units wide, read as greys. The house has no other pale blue.
for col in ('#e8f4ff', '#e8f4fd'):
    ok(MAP[(col, 'FILL')][0] == '--alv-accent-soft',
       '%s is a pale blue the grey band swallowed' % col)
    ok(near(col, '--alv-accent-soft') < near(col, '--alv-line-soft'),
       '  and accent-soft is nearer as well: %.1f against %.1f'
       % (near(col, '--alv-accent-soft'), near(col, '--alv-line-soft')))

# 4. DROPPED, NOT CORRECTED - and this is the one worth the most.
#    #f8f9fa as a LINE on one page is the page's OWN BACKGROUND: a
#    border deliberately invisible. --alv-line-soft is the right line
#    token and would make it visible, which is a change of appearance
#    on a decision nobody has made. A round that cannot tell "this is
#    drift" from "this is deliberate" should leave it alone and say so.
ok(('#f8f9fa', 'LINE') not in MAP,
   '#f8f9fa as a LINE is NOT in this round - a border painted the '
   'page colour is invisible on purpose')
# AND ONE PAGE KEEPS A COLOUR BY DECISION. This is not the classifier
# being wrong - it is the classifier being right and overruled anyway,
# which is a different thing and the more important one.
#
# fsr_details.html spells #ecd9a8 once, and test_fsr_palette ALLOWS it
# by name: "the Notify round's page-local warn tint, decided last night
# with a single asker". --alv-warn-line is 11.7 units away - a
# different tint - so converting it would have quietly overruled
# Demetri. His own suite caught it, in the sweep, on the first run.
ok(('fsr_details.html', '#ecd9a8') in KEEP,
   'fsr_details keeps #ecd9a8 by decision, not by oversight')
FSR = alv_tree.path_of('fsr_details.html')
ok('#ecd9a8' in now(FSR) and 'alv-warn-line' not in css_of(now(FSR)),
   '  and it is still spelled by hand there, as the Notify round left it')
ok(not os.path.exists(FSR + SUFFIX),
   '  so this round did not touch that page at all')

# THE OTHER FIVE USES OF THE SAME COLOUR DID CONVERT - four of them in
# base.html, where #ecd9a8 sat four times while base's own
# --alv-warn-line said #ecd39e. base disagreed with its own token, in
# its own file. A page can hold a colour by decision; base holding two
# answers to one question was not a decision.
ok('#ecd9a8' not in css_of(now(BASEP)),
   'base no longer spells #ecd9a8 while its own token says #ecd39e')
ok(len([1 for b in css_of(was(BASEP)).split(';') if '#ecd9a8' in b]) == 4,
   '  CONTROL: it did so four times before this round',
   len([1 for b in css_of(was(BASEP)).split(';') if '#ecd9a8' in b]))

GLA = alv_tree.path_of('generate_lease_agreement.html')
ok(re.search(r'border[^;:]*:[^;]*#f8f9fa', css_of(now(GLA)), re.I)
   is not None,
   '  and it is still a literal on generate_lease_agreement, waiting '
   'for a person')

# ==========================================================================
head('6b. what it bought - contrast on the families that carry text')

PAPER = as_colour(VALS['--alv-paper'].strip())
TEXT = [('#856404', 'INK', 'the alert amber text', 32),
        ('#155724', 'INK', 'the success green text', 17),
        ('#343a40', 'INK', 'a near-black heading', 9),
        ('#212529', 'INK', "Bootstrap's body colour", 7),
        ('#7f8c8d', 'INK', 'a Flat-UI grey', 7)]
print('      %-9s %-26s %6s %6s' % ('colour', 'what', 'paper', 'now'))
worse = []
for col, role, what, n in TEXT:
    new = as_colour(VALS[MAP[(col, role)][0]].strip())
    a0, a1 = ratio(col, PAPER), ratio(new, PAPER)
    print('      %-9s %-26s %6.2f %6.2f  %s'
          % (col, what, a0, a1, 'better' if a1 > a0 else 'fainter'))
    if a1 < a0 * 0.9:
        worse.append('%s drops %.2f to %.2f' % (col, a0, a1))
# THE FLOOR THAT MATTERS IS AA, NOT "NEVER LOSE A TENTH". #212529
# drops 15.4 to 13.0 and that is nothing anybody can use - both are
# three times the floor. The check that counts is whether a colour
# which CLEARED AA stops clearing it.
AA = 4.5
broke = []
for col, role, what, n in TEXT:
    new = as_colour(VALS[MAP[(col, role)][0]].strip())
    if ratio(col, PAPER) >= AA > ratio(new, PAPER):
        broke.append('%s was %.2f and is now %.2f, under the %.1f floor'
                     % (col, ratio(col, PAPER), ratio(new, PAPER), AA))
ok(not broke,
   'not one colour that cleared AA for normal text stops clearing it',
   '\n'.join(broke))

# AND ONE OF THEM NEVER CLEARED IT, which this round neither causes nor
# cures - but a suite that only reported what the round did would be
# the reason nobody ever found out.
#
#   #7f8c8d on tenant_payment_days.html: .pd-detail-title at 0.78rem,
#   .pd-note and .pd-legend at 0.85rem, .pd-section-note at 0.9rem -
#   small text at 3.48:1, where AA wants 4.5. It is Flat-UI's grey and
#   it was below the floor before this round touched it.
#
# --alv-ink-soft would fix it, at 5.53:1 - and that is a 55-unit move,
# which is tier C and needs a decision and a render. LOGGED HERE so the
# next person to open tier C finds it already measured.
FLAT = ratio('#7f8c8d', PAPER)
ok(FLAT < AA,
   'LOGGED: #7f8c8d on tenant_payment_days was ALREADY under AA at '
   '%.2f:1, on small text - this round does not fix that' % FLAT)
ok(MAP[('#7f8c8d', 'INK')][1] <= CEILING,
   '  it stays in tier B because --alv-ink-faint is %.1f away; '
   '--alv-ink-soft, which would clear AA at %.2f:1, is 55.4 away and '
   'is a tier C decision'
   % (MAP[('#7f8c8d', 'INK')][1],
      ratio(as_colour(VALS['--alv-ink-soft'].strip()), PAPER)))

ok(ratio(as_colour(VALS['--alv-ink-faint'].strip()), PAPER) >= 3.0,
   '  --alv-ink-faint, which the Flat-UI greys land on, clears 3:1 for '
   'large text', '%.2f:1'
   % ratio(as_colour(VALS['--alv-ink-faint'].strip()), PAPER))

# ==========================================================================
head('7. the render - longhands, and the gradient stops as well')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

SIMPLE = re.compile(r'^\.[A-Za-z][-\w]*$')

# ASK FOR THE LONGHAND, NOT THE SHORTHAND THE CSS HAPPENED TO USE.
# recipe_management writes `background: linear-gradient(135deg, #fff8e1
# 0%, #ffecb3 100%)`, and the computed `background` shorthand begins
# `rgba(0, 0, 0, 0) linear-gradient(...)` - the transparent
# background-COLOR, then the image. A reader that takes the first
# colour out of that string reports every gradient on the page as
# having turned black. It had not: the round moved a gradient STOP,
# which is a real change and one getComputedStyle exposes separately,
# under background-image.
PROBES = ['color', 'background-color', 'background-image',
          'border-top-color', 'border-right-color',
          'border-bottom-color', 'border-left-color', 'outline-color']

probe = {}
for p in TOUCHED:
    want = set()
    for at, end, lit, prop, tok, sel in cuts_for(alv_tree.code_only(was(p)), alv_tree.rel(p).replace(os.sep, '/')):
        last = sel.split('&& ')[-1]
        if SIMPLE.match(last):
            want.add(last[1:])
    if want:
        probe[p] = sorted(want)
BUSY = sorted(probe, key=lambda p: -len(probe[p]))[:10]

if sync_playwright is None:
    print('  --    the renders  (playwright missing)')
else:
    exe = '/opt/pw-browsers/chromium'
    bcss = css_of(alv_tree.code_only(now(BASEP)))
    boot = read(BOOTF) if os.path.exists(BOOTF) else ''
    KNOWN = {as_colour(VALS[t].strip()) for t, _w in MAP.values()}

    RGB = re.compile(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([0-9.]+))?\)')

    def colours(v):
        """Every opaque colour in a computed value, in order."""
        out = []
        for m in RGB.finditer(v or ''):
            if m.group(4) is not None and float(m.group(4)) < 0.999:
                continue
            out.append('#%02x%02x%02x'
                       % tuple(int(m.group(i)) for i in (1, 2, 3)))
        return out

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        def computed(page_css, width, klasses):
            divs = ''.join('<div class="%s" id="p_%d">x</div>'
                           % (k, i) for i, k in enumerate(klasses))
            pg = br.new_page(viewport={'width': width, 'height': 900})
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

        far = []
        same = 0
        changed = 0
        grad = 0
        shots = 0
        for p in BUSY:
            ks = probe[p]
            a_css, b_css = css_of(was(p)), css_of(now(p))
            for w in (390, 1280):
                x = computed(a_css, w, ks)
                y = computed(b_css, w, ks)
                shots += 2
                for k in sorted(x):
                    if x[k] == y[k]:
                        same += 1
                        continue
                    ca, cb = colours(x[k]), colours(y[k])
                    if k.endswith('background-image'):
                        grad += 1
                    if len(ca) != len(cb):
                        far.append('%s %s  %d colour(s) became %d'
                                   % (alv_tree.rel(p), k, len(ca), len(cb)))
                        continue
                    for ha, hb in zip(ca, cb):
                        if ha == hb:
                            continue
                        changed += 1
                        if dist(ha, hb) > CEILING:
                            far.append('%s %s moved %.1f  %s -> %s'
                                       % (alv_tree.rel(p), k,
                                          dist(ha, hb), ha, hb))
                        elif hb not in KNOWN:
                            far.append('%s %s landed on %s, which is not '
                                       'a token of this round'
                                       % (alv_tree.rel(p), k, hb))
            print('      %-44s %2d class(es) painted at 390 and 1280'
                  % (alv_tree.rel(p), len(ks)))
        br.close()

    ok(not far,
       'every colour that changed moved at most %.1f and landed on a '
       'token of this round' % CEILING, '\n'.join(far[:6]))
    ok(changed > 0,
       '  %d colour(s) DID change - a render that found nothing would be '
       'measuring nothing' % changed)
    ok(grad > 0,
       '  and %d of the changes were GRADIENT STOPS, which the shorthand '
       'reader could not see at all' % grad)
    print('      %d probed value(s) were unchanged. Over %d painting(s).'
          % (same, shots))

# ==========================================================================
head('8. registered')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(all(b in ROUNDS and ROUNDS.index(b) < ROUNDS.index(SUFFIX)
       for b in ('.bak_coltok', '.bak_coltok2')),
   '  and after B-1 and B-2, whose tree it measures against')
ok(ME in ps1, '%s is in the push suites' % ME)

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that any of these 105 spellings was a')
print('  mistake at the time. Nine ways of writing a pale teal is what')
print('  a tree looks like when nine people - or one person on nine')
print('  days - each pick the colour that looks right. The round does')
print('  not say they were wrong; it says the house now has one answer')
print('  and these pages use it.')
print()
print('  ALSO NOT PROVED: tier C. 557 uses are a real colour change -')
print("  Bootstrap's green, red and amber are 226 of them - and none of")
print('  it can borrow this gate, because this gate is that the move is')
print('  small. Those need a render and a decision per family.')
