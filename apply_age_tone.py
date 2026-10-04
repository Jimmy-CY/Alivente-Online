# -*- coding: utf-8 -*-
"""AG-1 - THE AGEING SCALE COMES BACK INTO THE THEME

Demetri, 4 Oct 2026, of the Outstanding Invoices Report: "I don't like
these colours any more. They don't fit within our team and grey theme. I
want you to give suggestions how we can tone this down to fit in. I have
decided that I don't need a green and red scale. Also, the total
outstanding figures must not be in blue, but fit into our standard."

Two decisions, both his, taken after the suggestions:
    ONE TONE, DEEPENING - not green to red
    THE FIGURE TAKES THE HOUSE ACCENT, UNDERLINED - not blue

==========================================================================
WHAT WAS THERE: FIVE HUES ACROSS A ROW
==========================================================================
    age-0  #1e7d4f green    on #e6f4ec
    age-1  #8a7a12 olive    on #fdf8e6
    age-2  #8e6207 amber    on #fbeec9
    age-3  #a8481a rust     on #f8e0cd
    age-4  #b3261e red      on #f6d5d2

Six columns of a report, each a different hue, in an application whose
palette is one teal and a run of greys. It read as a traffic light
bolted onto a ledger.

AND A TRAFFIC LIGHT IS THE WRONG PICTURE HERE. Green/red says healthy
versus broken. Ageing is not that: money forty days late is not a
different KIND of thing from money ten days late, it is the same thing
further along. One tone that deepens says exactly that, and says it to a
reader who cannot separate the hues as well.

==========================================================================
THE SCALE: ONE WARM NEUTRAL, FIVE STEPS
==========================================================================
                              ink on the tint
    age-0  #fafaf9              12.40
    age-1  #f2f1ee              11.47
    age-2  #e8e5df              10.30
    age-3  #dcd7cd               9.03
    age-4  #cdc6b9               7.63

measured against --alv-ink, which is what the figures in those cells are
written in. Every step clears AA by a wide margin; the old scale's tints
carried coloured ink at 4.05 to 4.78.

WARM, NOT THE GREY ALREADY IN THE PALETTE. --alv-surface and
--alv-surface-deep are the page's own wash and are used for panels and
headers all over this app; an ageing cell has to be legible AS a tint
beside them, and a cool grey column on a cool grey page is invisible. A
warm neutral is still "the grey theme" and still separable.

==========================================================================
THE PILL KEEPS ITS INK, AND GAINS AN EDGE
==========================================================================
.alv-age-pill wrote its text in --age. Carried over literally, the two
palest steps would have put #8a979d and #8a8578 on their own tints -
2.87 and 3.26, both failing AA on text that is there to be read.

So the pill's TEXT is --alv-ink at every step, and the step shows in the
background and in a 1px border of --age. The signal is doubly encoded and
nothing is below 7.6.

--age itself still deepens, because it drives the DOT and the BAR FILL,
which are shapes rather than text: 3.00 to 11.80 against paper, the
lowest exactly on the 3:1 that non-text needs.

==========================================================================
AND THE FIGURE IS NOT BLUE
==========================================================================
    .clickable-amount        color: var(--alv-edit)   #2563eb  the pencil blue
    the phone card's total   color: #007bff           raw Bootstrap

Two different blues for one number, neither of them this app's colour.
Both become --alv-accent, underlined - 4.91 on paper, and the underline
is what says it can be pressed, so the colour is not carrying that alone.
--alv-edit is the colour of a PENCIL in this app; a figure you click to
look at a breakdown does not edit anything.

Backups: .bak_agetone. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_agetone'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

BASE = alv_tree.path_of('base.html')
OIR = alv_tree.path_of('open_invoices_report.html')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('AG1: %s is not a byte copy' % bak)


def swap(nl, old, new, what):
    c = nl.count(old)
    if c != 1:
        raise SystemExit('AG1: %s appears %d times, not once' % (what, c))
    return nl.replace(old, new)


print('=' * 74)
print('AG-1 - ONE TONE, DEEPENING%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. THE TOKENS.
# ==========================================================================
t, raw = read(BASE)
nl = t.replace('\r\n', '\n')

OLD_T = """        --alv-age-1:      #8a7a12;
        --alv-age-1-soft: #fdf8e6;
        --alv-age-2:      #8e6207;
        --alv-age-2-soft: #fbeec9;
        --alv-age-3:      #a8481a;
        --alv-age-3-soft: #f8e0cd;
        --alv-age-4:      #b3261e;
        --alv-age-4-soft: #f6d5d2;
"""

NEW_T = """        /* AG-1, 4 Oct 2026 - ONE TONE, DEEPENING. Demetri, of the
           Outstanding Invoices Report: "I don't like these colours any
           more. They don't fit within our team and grey theme... I have
           decided that I don't need a green and red scale."

           WHAT THIS REPLACED, named so it is never re-derived: #8a7a12
           olive, #8e6207 amber, #a8481a rust and #b3261e red, with
           #fdf8e6 / #fbeec9 / #f8e0cd / #f6d5d2 beneath them, and
           --alv-good standing in for step 0. Six columns of one report,
           each a different hue, in an application whose palette is one
           teal and a run of greys.

           AND THE TRAFFIC LIGHT WAS THE WRONG PICTURE. Green to red
           says healthy versus broken. Money forty days late is not a
           different KIND of thing from money ten days late - it is the
           same thing further along, which is what one deepening tone
           says, and says to a reader who cannot separate hues too.

           WARM, NOT THE GREY ALREADY HERE. --alv-surface and
           --alv-surface-deep are this page's own wash; an ageing column
           has to read AS a tint beside them, and cool grey on cool grey
           does not. Warm is still the grey theme and still separable.

           MEASURED AGAINST --alv-ink, which is what the figures in
           these cells are written in:
               step 0  12.40    step 1  11.47    step 2  10.30
               step 3   9.03    step 4   7.63
           The scale this replaced carried coloured ink at 4.05 to 4.78.

           THE SOLID TOKEN STILL DEEPENS because it drives the DOT and
           the BAR FILL, which are shapes, not text: 3.00 to 11.80
           against paper, the lowest exactly on the 3:1 non-text needs.
           It is NOT the pill's text colour any more - see .alv-age-pill,
           where carrying it over literally would have put #8a8578 on
           #f2f1ee at 3.26. */
        --alv-age-0:      #8a979d;
        --alv-age-0-soft: #fafaf9;
        --alv-age-1:      #8a8578;
        --alv-age-1-soft: #f2f1ee;
        --alv-age-2:      #6f6a5d;
        --alv-age-2-soft: #e8e5df;
        --alv-age-3:      #55504a;
        --alv-age-3-soft: #dcd7cd;
        --alv-age-4:      #3b3733;
        --alv-age-4-soft: #cdc6b9;
"""

OLD_C = """.alv-age-0 { --age: var(--alv-good);   --age-soft: var(--alv-good-soft); }
.alv-age-1 { --age: var(--alv-age-1);  --age-soft: var(--alv-age-1-soft); }"""
NEW_C = """/* AG-1 - step 0 is the TOP OF THIS SCALE now, not the good token. It
   used to be --alv-good literally, which is how a ledger column came to
   be green. Not ageing is the absence of ageing, not a health verdict. */
.alv-age-0 { --age: var(--alv-age-0);  --age-soft: var(--alv-age-0-soft); }
.alv-age-1 { --age: var(--alv-age-1);  --age-soft: var(--alv-age-1-soft); }"""

OLD_P = """.alv-age-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
    background: var(--age-soft, var(--alv-neutral-soft));
    color: var(--age, var(--alv-ink));
}"""
NEW_P = """/* AG-1, 4 Oct 2026 - THE TEXT IS --alv-ink AT EVERY STEP. It was
   var(--age), and with a one-tone scale that put #8a979d on #fafaf9 and
   #8a8578 on #f2f1ee - 2.87 and 3.26, both failing AA on a pill that
   exists to be read. The STEP shows in the background and in a 1px
   border of --age, so it is encoded twice and nothing is under 7.6. */
.alv-age-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
    background: var(--age-soft, var(--alv-neutral-soft));
    border: 1px solid var(--age, var(--alv-line));
    color: var(--alv-ink);
}"""

if 'AG-1, 4 Oct 2026' in nl:
    print('  base.html                  already one deepening tone')
else:
    nl = swap(nl, OLD_T, NEW_T, 'the ageing tokens')
    nl = swap(nl, OLD_C, NEW_C, 'the step-0 class')
    nl = swap(nl, OLD_P, NEW_P, 'the ageing pill')
    out = nl.replace('\n', '\r\n') if CRLF.get(BASE) else nl
    if not CHECK:
        back_up(BASE, raw)
        write(BASE, out)
    print('  base.html                  5 hues -> 1 tone, pill ink on --alv-ink')

# ==========================================================================
# 2. THE FIGURE.
# ==========================================================================
o, oraw = read(OIR)
onl = o.replace('\r\n', '\n')

OLD_F = """.clickable-amount {
    cursor: pointer;
    transition: background-color 0.2s ease;
    text-decoration: underline;
    color: var(--alv-edit);
}"""
NEW_F = """/* AG-1, 4 Oct 2026 - Demetri: "the total outstanding figures must not
   be in blue, but fit into our standard." It was --alv-edit, which is
   #2563eb - the colour of a PENCIL in this app. A figure you press to
   see a breakdown does not edit anything. --alv-accent measures 4.91 on
   paper, and the underline below is what says it can be pressed, so the
   colour is not carrying that on its own. */
.clickable-amount {
    cursor: pointer;
    transition: background-color 0.2s ease;
    text-decoration: underline;
    color: var(--alv-accent);
}"""

if 'AG-1, 4 Oct 2026' in onl:
    print('  open_invoices_report.html  already on the house accent')
else:
    onl = swap(onl, OLD_F, NEW_F, 'the clickable amount')
    # THE PHONE CARD'S TOTAL WAS A SECOND, DIFFERENT BLUE - raw #007bff,
    # Bootstrap's, so one number wore two colours depending on screen.
    onl = swap(onl, '        color: #007bff;\n',
               '        /* AG-1 - raw #007bff, Bootstrap\'s own, so the same\n'
               '           total read in two different blues depending on\n'
               '           which screen you held. */\n'
               '        color: var(--alv-accent);\n',
               "the phone card's total")
    out = onl.replace('\n', '\r\n') if CRLF.get(OIR) else onl
    if not CHECK:
        back_up(OIR, oraw)
        write(OIR, out)
    print('  open_invoices_report.html  2 blues -> --alv-accent')

# ==========================================================================
# 3. THE CHART'S FALLBACKS, WHICH ARE A COPY OF THE SCALE.
# ==========================================================================
# fsr.html reads the tokens at runtime and carries a hard-coded fallback
# for each, for the case where a stylesheet has not loaded. Three of
# those fallbacks ARE the old scale, written out. Left alone they would
# be the only place the green-to-red ramp still lived, and
# test_ia_palette compares every one of them against base - which is how
# this was found rather than shipped.
FSR = alv_tree.path_of('fsr.html')
f, fraw = read(FSR)
fnl = f.replace('\r\n', '\n')
OLD_FB = """  var GOOD    = iaTok('good',         '#1e7d4f'),
      WARN    = iaTok('age-2',        '#8e6207'),
      SERIOUS = iaTok('age-3',        '#a8481a'),
      CRIT    = iaTok('age-4',        '#b3261e'),"""
NEW_FB = """  // AG-1, 4 Oct 2026 - the three ageing fallbacks follow the scale.
  // They were #8e6207 / #a8481a / #b3261e, which IS the green-to-red
  // ramp written out a second time; a fallback that disagrees with the
  // token it stands in for is the old design hiding behind the new one.
  var GOOD    = iaTok('good',         '#1e7d4f'),
      WARN    = iaTok('age-2',        '#6f6a5d'),
      SERIOUS = iaTok('age-3',        '#55504a'),
      CRIT    = iaTok('age-4',        '#3b3733'),"""

if 'AG-1, 4 Oct 2026' in fnl:
    print('  fsr.html                   fallbacks already follow the scale')
else:
    fnl = swap(fnl, OLD_FB, NEW_FB, "the chart's ageing fallbacks")
    out = fnl.replace('\n', '\r\n') if CRLF.get(FSR) else fnl
    if not CHECK:
        back_up(FSR, fraw)
        write(FSR, out)
    print('  fsr.html                   3 fallbacks follow the new scale')

# ==========================================================================
# 4. THE SUITES THAT HELD THE OLD DESIGN - REPAIRED HERE, NOT BY HAND.
# ==========================================================================
# Each of these made a TRUE claim about the scale this round replaces.
# None of them is wrong; each is out of date, and the round that made it
# out of date is the round that owes the repair.
REPAIRS = [
    # base's own contents page states how many tokens it owns, and
    # test_standards_doc counts them. This round adds --alv-age-0 and
    # its soft variant - step 0 used to BE --alv-good, literally, which
    # is how a ledger column came to be green - so the count moves from
    # 78 to 80. A number a file states about itself has to be true.
    ('pages/templates/base.html',
     """  78 design tokens and the component classes below.""",
     """  80 design tokens and the component classes below."""),

    # test_countdown_tone holds that a countdown to a birthday must not
    # be drawn on the ageing scale, and gives the reason: that scale is
    # SEVERITY, and it has a failure red at the top. AG-1 removes the
    # red. The conclusion is unchanged and the reason has to be
    # restated, not deleted - a rule whose reason has quietly stopped
    # being true is a rule somebody repeals next year.
    ('test_countdown_tone.py',
     """ok('--alv-age-4:      #b3261e;' in base,
   '  with #b3261e at the top of it - the same red as a failure')""",
     """# AG-1, 4 Oct 2026 - THE REASON MOVED, THE RULE DID NOT. This used
# to read `'--alv-age-4:      #b3261e;' in base` - the scale ended in a
# failure red, so putting a birthday on it said a birthday was a
# failure. Demetri: "I have decided that I don't need a green and red
# scale", and the red is gone.
#
# A countdown still must not use it, and now for a plainer reason: the
# scale is a DEPTH, four steps of one tone that only ever get heavier.
# Days until a birthday do not get heavier - they run out and start
# again. So what is held here is that the scale is monotonic and
# one-way, which is exactly what a countdown is not.
_ages = re.findall(r'--alv-age-([1-4]):\\s*(#[0-9a-fA-F]{6})', base)
ok(len(_ages) == 4, '  and that scale has four steps', _ages)


def _lum_ag(h):
    c = [int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
         for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


_l = [_lum_ag(h) for _, h in sorted(_ages)]
ok(_l == sorted(_l, reverse=True),
   '  that only ever gets heavier - which a countdown does not, because '
   'it runs out and starts again',
   ['%.3f' % x for x in _l])"""),

    # test_meal_row compares base's literal-colour count against its own
    # backup, to hold that ML-1 added a name and no new colour. True, and
    # it read `code_only(read(BASE))` - THE LIVE FILE - against a frozen
    # backup, so any later round touching base broke a true claim about a
    # round that had done its job. AG-1 adds --alv-age-0 and its soft
    # variant, step 0 having been --alv-good literally, and the count
    # went 134 -> 136.
    #
    # FIFTH INSTANCE OF THIS SHAPE. test_passport_filter yesterday,
    # test_entry_sections an hour ago, and three before those. now() is
    # already defined in this file, two hundred lines above; it was
    # simply not used on this line.
    ('test_meal_row.py',
     """BS = code_only(read(BASE))""",
     """# AG-1, 4 Oct 2026 - now(), not read(). This was the LIVE file
# compared against a frozen backup, so a later round touching base broke
# a true claim about ML-1. now() is as_left_by: base as ML-1 left it.
BS = code_only(now(BASE))"""),

    # test_ageing_scale held the scale's ENDS to the semantic tokens -
    # step 2 is warn, step 4 is bad - so a hue scale could not drift away
    # from the meanings beside it. AG-1 severs that on purpose: the scale
    # is not semantic any more, it is a depth. The invariant that
    # replaces it is the one a depth has.
    ('test_ageing_scale.py',
     """check('step 2 IS the warn colour, so the scale cannot drift from the '
      'semantics beside it',
      _tokval('--alv-age-2') is not None
      and _tokval('--alv-age-2') == _tokval('--alv-warn'))
check('step 4 IS the bad colour',
      _tokval('--alv-age-4') is not None
      and _tokval('--alv-age-4') == _tokval('--alv-bad'))""",
     """# AG-1, 4 Oct 2026 - THE ANCHOR IS GONE, DELIBERATELY. These two
# checks used to hold step 2 to --alv-warn and step 4 to --alv-bad, so a
# green-to-red scale could not drift away from the meanings beside it.
# That was the right invariant for a scale made of hues. Demetri: "I have
# decided that I don't need a green and red scale."
#
# A DEPTH HAS A DIFFERENT INVARIANT. The scale no longer says healthy or
# broken - it says near or far - so what has to hold is that it is ONE
# TONE and that it only ever goes one way. Anchoring it to warn and bad
# now would re-introduce the hues by the back door.
check('step 2 is NOT the warn colour - the scale is a depth, not a verdict',
      _tokval('--alv-age-2') is not None
      and _tokval('--alv-age-2') != _tokval('--alv-warn'))
check('  nor step 4 the bad one',
      _tokval('--alv-age-4') is not None
      and _tokval('--alv-age-4') != _tokval('--alv-bad'))
_spread = lambda h: (max(int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))
                     - min(int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)))
check('  and every step is a neutral, which is what replaces the anchor',
      all(_tokval('--alv-age-%d' % _s) and _spread(_tokval('--alv-age-%d' % _s)) <= 25
          for _s in (1, 2, 3, 4)),
      str([_tokval('--alv-age-%d' % _s) for _s in (1, 2, 3, 4)]))"""),

    # test_ia_tiles and test_fsr_palette both asked that the four ageing
    # chips render in four DIFFERENT inks. Under a hue scale that was the
    # whole point. Under one tone the ink is --alv-ink at every step on
    # purpose, because the two palest steps could not carry their own
    # colour as text and clear AA. The step is in the TINT now, so that
    # is what these ask.
    ('test_ia_tiles.py',
     """    _seen = [D['chips'][k]['color'] for k in ('a0', 'a2', 'a3', 'a4')]
    check('all four ageing chips paint a DIFFERENT colour',
          len(set(_seen)) == 4, str(_seen))""",
     """    # AG-1, 4 Oct 2026 - THE INK IS THE SAME AT EVERY STEP NOW, and
    # that is the design rather than a regression. A one-tone scale that
    # also coloured its text would have put #8a979d on #fafaf9 - 2.87,
    # failing AA on a chip that exists to be read. The STEP moved into
    # the tint, so the tint is what has to differ.
    _seen = [D['chips'][k]['color'] for k in ('a0', 'a2', 'a3', 'a4')]
    _tint = [D['chips'][k]['bg'] for k in ('a0', 'a2', 'a3', 'a4')]
    check('all four ageing chips paint a DIFFERENT tint',
          len(set(_tint)) == 4, str(_tint))
    check('  and one ink, which is what one tone means',
          len(set(_seen)) == 1, str(_seen))"""),

    ('test_fsr_palette.py',
     """        inks = [g['color'] for g in got[:4]]
        check('the four ages render in FOUR different inks',
              len(set(inks)) == 4, str(inks))""",
     """        # AG-1, 4 Oct 2026 - FOUR TINTS, ONE INK. This asked for four
        # different inks, which was right while the scale was four
        # hues. One tone puts the step in the background, because the
        # palest steps cannot carry their own colour as text and clear
        # AA - 2.87 at step 0.
        inks = [g['color'] for g in got[:4]]
        tints = [g['bg'] for g in got[:4]]
        check('the four ages render in FOUR different tints',
              len(set(tints)) == 4, str(tints))
        check('  on one ink, which is what one tone means',
              len(set(inks)) == 1, str(inks))"""),

    ('test_fsr_palette.py',
     """        check('  .. and 257 days does NOT, which is the whole point',""",
     """        # AND THE SAME SUBSTITUTION HERE: the two halves of the defect
        # are still the two halves, but a band now shows in the tint.
        _same = [dict(g, color=g['bg']) for g in _same]
        check('  .. and 257 days does NOT, which is the whole point',"""),
]

for name, old, new in REPAIRS:
    path = os.path.join(ROOT, name)
    if not os.path.isfile(path):
        print('  %-26s not on disk - skipped' % name)
        continue
    t2, raw2 = read(path)
    n2 = t2.replace('\r\n', '\n')
    # DONE IS DECIDED BY A MARKER UNIQUE TO THIS REPAIR, and this loop
    # has now been wrong in both of the other two ways.
    #
    #   "the new text's first line is present" skipped a later repair
    #   whose first line was `AMENDED = {`, already in the file.
    #
    #   "the anchor is gone" re-applied a repair whose anchor SURVIVES
    #   inside its own replacement - the new code still contains
    #   `want[a_sel][a_key] = a_now`, one branch deeper - so the second
    #   run nested it again and left the file with a SyntaxError.
    #
    # The marker is the first line of the comment each repair writes,
    # which exists nowhere else.
    marker = next((l.strip() for l in new.split('\n')
                   if l.strip().startswith('#') and len(l.strip()) > 12),
                  new.strip()[:60])
    if marker in n2:
        print('  %-26s already repaired' % name)
        continue
    c = n2.count(old)
    if c != 1:
        raise SystemExit('AG1: %s - the claim to repair appears %d times, '
                         'not once' % (name, c))
    n2 = n2.replace(old, new)
    out = n2.replace('\n', '\r\n') if CRLF.get(path) else n2
    if not CHECK:
        back_up(path, raw2)
        write(path, out)
    print('  %-26s claim brought up to date' % name)

print('=' * 74)
print('AG-1 %s' % ('would apply' if CHECK else 'applied'))
print('=' * 74)
