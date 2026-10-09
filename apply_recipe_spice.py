# -*- coding: utf-8 -*-
"""apply_recipe_spice.py - Section RC round RC-2, 9 Oct 2026.

THE RECIPE MODULE'S ORANGES BECOME A HOUSE FAMILY.

Nine live pairs on the recipe pages read below AA because white text
sits on Bootstrap's warning yellow or orange. Four of them are at
1.63:1 and three at 2.57:1 - that is not low contrast, it is invisible
text, and two of them are an Edit button and a Save button:

    .recipe-edit-btn                          white on #ffc107  1.63
    .recipe-card-actions-mobile .recipe-edit  white on #ffc107  1.63
    .conv-preset-btn:hover                    white on #ffc107  1.63
    .nm-conversion-form .nm-preset-btn:hover  white on #ffc107  1.63
    .conv-row-unit                            white on #fd7e14  2.57
    .btn-save                                 white on #fd7e14  2.57
    .tag-protein                              white on #fd7e14  2.57
    .recipe-list-tag.protein                #e65100 on #fdf3dd  3.44
    .book-detail-tag.protein                #e65100 on #fdf3dd  3.44

Every number above came out of apply_edit_ink.census(), the pair table
B-4b built - not out of a regex of mine. My own first survey of this
round undercounted the list at seven and missed a tenth site whose
text colour is set on the base selector rather than the modifier that
carries the fill, which the census cannot pair either. That site is
.ai-suggestion-type-icon.reduce and it is converted here by name.

THE FAMILY, AND WHY IT IS NOT AN EXISTING ONE
---------------------------------------------
    --alv-spice        #a8481a   white on it   5.82   AA
    --alv-spice-ink    #8a3f08   on paper      7.51   AA
    --alv-spice-soft   #fdf0e4   ink on it     6.71   AA
    --alv-spice-line   #f0d7bd   borders

Not --alv-warn: warn means caution, and these are an Edit button, a
Save button and a protein tag. Reusing it would make every one of them
read as an alert. Not --alv-grade-4 or --alv-tag-clay-*: grade-4 means
a grade on a five-point scale and clay is a tag identity, and the
fills need a solid that carries white, which the clay family has no
member for.

A CONSTRAINT WORTH RECORDING. There is no true orange that carries
white at the ratio the house holds its other solids to. Ten candidates
were measured; everything light enough to read as orange rather than
brown falls under 5.0 against white, and everything clearing 5.2 lands
on top of --alv-grade-4 (#a8481a). Orange at this standard IS burnt
sienna, so --alv-spice takes grade-4's value deliberately rather than
by accident, and the two tokens are documented as sharing it.

THE MAP IS BY WHAT THE DECLARATION MEANS, NOT BY ITS VALUE
----------------------------------------------------------
#ffc107 appears on these six pages as three different things: the fill
of a button with white text, the fill of a pill with dark ink, and a
text highlighter. One literal, three jobs, three different tokens. A
map keyed on (colour, role) the way B-3's is would collapse them, so
this round's map is explicit per site and every entry carries its
reason.

WHAT THIS ROUND LEAVES, AND WHY
-------------------------------
  22  THE COOKBOOK THEME on recipe_management.html - #5c3a2a twelve
      times, #2c1810 five, #f5e6d0 twice, #e8d9c0 and #8a6545. Counted
      three times before it was right: 16 by hand off a truncated
      dump, 17 once measured, and 22 once #2c1810 was recognised as
      part of the theme rather than only as the ink of a count badge
      on another page. A recipe book styled
      to look like a book: page edges, step numbers, layout buttons.
      That is a deliberate sub-theme, not drift, and spice would
      destroy it. A candidate for its own --alv-book-* family if he
      ever wants it in the house; not this round's to take.
   1  .recipe-list-favourite-btn - #ccc on white at 1.61. A grey
      stray, not an orange. Belongs to the B-5 grey tail.
   1  .recipe-list-tag.course - #1976d2 on accent-soft at 4.04. Blue.
      B-7's.
   2  .recipe-list-tag.category and .ai-goal-card-icon - the accent on
      a tint at 4.31 and 4.20. Part of the eighteen-pair accent-on-
      tint base decision still open; a page fix here would pre-empt a
      decision that belongs in base.
   1  .spell-error-context .highlight-word on preview_imported_recipe -
      a spell-check marker pen. B-4 PINNED THIS ONE DELIBERATELY in
      apply_amber.LEAVE_RULES with the reason "brightness IS the
      function", and RC-2's first draft converted it to
      --alv-warn-line without knowing. test_amber caught it and the
      round reverted: a highlighter that is not bright does not mark
      anything. The page is therefore not touched by this round at
      all, which is why five pages became four.
   4  the dark tooltip palette on ingredient_base_units_management -
      #374151, #9ca3af, #e5e7eb. Not warm, and a dark-surface palette
      has no house family yet.

NOT PROVED HERE: that the cookbook browns should stay browns. That is
an appearance decision and it was never put to him, because this round
does not touch them. Named so the absence is a choice on the record
and not an oversight.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_cssrules as R                                      # noqa: E402
import alv_tree as T                                          # noqa: E402
import apply_edit_ink as B                                    # noqa: E402

SUFFIX = '.bak_spice'
MARK = 'RC-2, 9 Oct 2026'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_recipe_spice.py'
ME = 'apply_recipe_spice.py'
CHECK = False

SPICE = (
    ('--alv-spice', '#a8481a',
     'the solid: white on it 5.82. Shares --alv-grade-4 value - there '
     'is no orange at this ratio that is not this colour'),
    ('--alv-spice-ink', '#8a3f08',
     'orange as text, and the hover partner of the solid: 7.51 on paper'),
    ('--alv-spice-soft', '#fdf0e4',
     'the tint under dark ink: 6.71 with spice-ink on it'),
    ('--alv-spice-line', '#f0d7bd',
     'borders on warm surfaces, and pale warm text on a dark ground'),
)


def read(p):
    return open(p, encoding='utf-8', newline='').read()


def write(p, t):
    open(p, 'w', encoding='utf-8', newline='').write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


# ---------------------------------------------------------------------
# THE MAP. Keyed (page, selector, property, literal) -> (new, family).
#
# TWO FAMILIES, NOT ONE. My first proposal painted every warm literal
# on these pages spice. Reading the rules said otherwise: most of them
# sit in a rule whose GROUND already declares a family, and only the
# literal had drifted. The tag sets prove it -
#
#     .recipe-list-tag.course      accent-soft + a blue literal
#     .recipe-list-tag.category    accent-soft + var(--alv-accent)
#     .recipe-list-tag.protein     warn-soft   + #e65100     <- drift
#     .recipe-list-tag.vegetarian  good-soft   + var(--alv-good)
#     .recipe-list-tag.author      accent-soft + var(--alv-accent-ink)
#
# - four siblings on house tokens and one on a literal. The protein
# chip belongs to WARN, because its own background says so. Painting
# it spice would have put one chip of a five-chip set in a family of
# its own. Same for .recipe-match-card.good-match, whose siblings are
# --alv-good and --alv-accent, and .nutrition-nudge, whose gradient
# starts at --alv-warn-soft.
#
# SPICE is for the sites where warm is the module's IDENTITY and not a
# caution: an Edit button, a Save button, a unit chip, the conversion
# wizard's own controls. --alv-warn would carry white at 5.38 and
# would have worked on contrast alone - it is refused on meaning.
# ---------------------------------------------------------------------
SPICE_FAM, WARN_FAM = 'spice', 'warn'

MAP = {
 'recipe_management.html': (
  ('.nutrition-nudge', 'background', '#ffecb3',
   'var(--alv-warn-line)', WARN_FAM,
   'the gradient partner of --alv-warn-soft, which starts this rule'),
  ('.nutrition-nudge', 'border', '#ffc107',
   'var(--alv-warn)', WARN_FAM,
   'siblings .perfect-match and .okay-match border on the solid'),
  ('.nutrition-nudge i.fa-info-circle', 'color', '#f57c00',
   'var(--alv-warn-ink)', WARN_FAM, 'the icon of a warn-ground box'),
  ('.recipe-edit-btn', 'background', '#ffc107',
   'var(--alv-spice)', SPICE_FAM,
   'FIXES 1.63 - white text on Bootstrap yellow, on an Edit button'),
  ('.recipe-list-tag.protein', 'color', '#e65100',
   'var(--alv-warn-ink)', WARN_FAM,
   'FIXES 3.44 - one chip of a five-chip set, ground already warn-soft'),
  ('.recipe-match-card.good-match', 'border-color', '#ffc107',
   'var(--alv-warn)', WARN_FAM,
   'ground is warn-soft and the two siblings border on their solid'),
  ('.book-detail-tag.protein', 'color', '#e65100',
   'var(--alv-warn-ink)', WARN_FAM, 'FIXES 3.44 - the same chip set'),
  ('.recipe-card-actions-mobile .recipe-edit-btn', 'background', '#ffc107',
   'var(--alv-spice)', SPICE_FAM, 'FIXES 1.63 - the phone override'),
 ),
 'view_recipe.html': (
  ('.tag-protein', 'background', '#fd7e14',
   'var(--alv-spice)', SPICE_FAM,
   'FIXES 2.57 - a filled chip with white text, not a warn ground'),
  ('.conv-input-group input[type="number"]:focus', 'border-color', '#fd7e14',
   'var(--alv-spice)', SPICE_FAM, 'the focus ring of a spice control'),
  ('.ai-suggestion-type-icon.reduce', 'background', '#fd7e14',
   'var(--alv-spice)', SPICE_FAM,
   'FIXES 2.57 that the census cannot see - the white comes from the '
   'base selector, not from this modifier, so pair_table never pairs '
   'them. Converted by name'),
  ('.ai-suggestion-change .reduction-note', 'color', '#fd7e14',
   'var(--alv-spice-ink)', SPICE_FAM, 'warm text on paper'),
 ),
 'unit_conversions_wizard.html': (
  ('.progress-bar-label .progress-main strong', 'color', '#fd7e14',
   'var(--alv-spice-ink)', SPICE_FAM, 'warm text on paper'),
  ('.progress-bar-label .progress-percent', 'color', '#fd7e14',
   'var(--alv-spice-ink)', SPICE_FAM, 'warm text on paper'),
  ('.progress-bar-fill', 'background', '#ffc107',
   'var(--alv-spice-ink)', SPICE_FAM, 'the gradient start - a bar, no text'),
  ('.progress-bar-fill', 'background', '#fd7e14',
   'var(--alv-spice)', SPICE_FAM, 'the gradient end'),
  ('.wizard-current-meta .fdc-link', 'color', '#fd7e14',
   'var(--alv-spice-ink)', SPICE_FAM, 'a link, warm, on paper'),
  ('.conv-row', 'border', '#ffc107',
   'var(--alv-spice-line)', SPICE_FAM, 'a hairline on a tinted row'),
  ('.conv-row-unit', 'background', '#fd7e14',
   'var(--alv-spice)', SPICE_FAM, 'FIXES 2.57 - white on the unit chip'),
  ('.conv-input-group input[type="number"]', 'border', '#ffc107',
   'var(--alv-spice)', SPICE_FAM,
   'a 2px control outline on paper: the line token reads 1.39 against '
   'white and would all but disappear, so a delineating border takes '
   'the solid'),
  ('.conv-input-group input[type="number"]:focus', 'border-color', '#fd7e14',
   'var(--alv-spice-ink)', SPICE_FAM, 'focus is the darker partner'),
  ('.conv-preset-btn', 'border', '#ffc107',
   'var(--alv-spice)', SPICE_FAM, 'a button outline on paper'),
  ('.conv-preset-btn:hover', 'background', '#ffc107',
   'var(--alv-spice)', SPICE_FAM, 'FIXES 1.63 - white on hover'),
  ('.conv-apply-to', 'border-top', '#ffc107',
   'var(--alv-spice-line)', SPICE_FAM, 'a dashed divider, decorative'),
  ('.btn-save', 'background', '#fd7e14',
   'var(--alv-spice)', SPICE_FAM, 'FIXES 2.57 - white text on Save'),
  ('.btn-save', 'border', '#fd7e14',
   'var(--alv-spice)', SPICE_FAM, 'its border matches its fill'),
  ('.btn-save:hover', 'background', '#e8590c',
   'var(--alv-spice-ink)', SPICE_FAM, 'the darker partner, 7.51 with white'),
  ('.btn-save:hover', 'border-color', '#d04e0a',
   'var(--alv-spice-ink)', SPICE_FAM, 'and its border follows'),
 ),
 'ingredient_base_units_management.html': (
  ('.page-action-buttons .btn .action-count-badge.badge-unconvertible',
   'background', '#ffc107', 'var(--alv-warn)', WARN_FAM,
   'a count of rows that cannot be converted - its siblings are '
   'var(--alv-bad) with white and a grey disabled, so the warn solid '
   'matches that shape. Its #2c1810 text moves to --alv-on-accent in '
   'the same rule. THE MODIFIER IS badge-unconvertible, not the '
   'count-warning I first guessed: the gate refused the whole round '
   'rather than write 41 of its 43 edits'),
  ('.nutrition-unmapped', 'border', '#ffeaa7',
   'var(--alv-warn-line)', WARN_FAM, 'a pale border on a status row'),
  ('.conversion-partial', 'border', '#ffeaa7',
   'var(--alv-warn-line)', WARN_FAM, 'the same, one row down'),
  ('.row-tooltip h6', 'color', '#ffd166',
   'var(--alv-warn-line)', WARN_FAM,
   'PALE WARM ON A DARK GROUND. The tooltip is background: '
   'var(--alv-ink), so an ink token here would be invisible - the '
   'line token reads 8.87 on it. The one site in this round where '
   'the dark/light logic runs backwards'),
  ('.nutrition-source-pill.source-manual', 'background', '#fde68a',
   'var(--alv-warn-soft)', WARN_FAM,
   'a ground my first orange filter missed entirely - pale yellow sat '
   'outside its saturation floor, so the pill was counted as a text '
   'colour with no ground'),
  ('.nutrition-source-pill.source-manual', 'color', '#78350f',
   'var(--alv-warn-ink)', WARN_FAM, 'and its ink, 7.34 on that ground'),
  ('.edit-mode td', 'border-bottom', '#ffc107',
   'var(--alv-spice)', SPICE_FAM,
   'an active-editing marker - state, not caution, and it has to stay '
   'visible against white'),
  ('.ingredients-table tbody tr.edit-mode', 'border-color', '#ffc107',
   'var(--alv-spice)', SPICE_FAM, 'the phone form of the same marker'),
  ('.nm-current-meta .nm-pill-unmapped', 'background', '#ffc107',
   'var(--alv-warn-soft)', WARN_FAM,
   'a pill carrying var(--alv-ink): the tint keeps it 11.75 and the '
   'ink needs no change'),
  ('.nm-conversion-panel', 'border', '#ffc107',
   'var(--alv-spice)', SPICE_FAM, 'the panel outline on paper'),
  ('.nm-conversion-form input[type="number"]', 'border', '#ffc107',
   'var(--alv-spice)', SPICE_FAM, 'a 2px control outline on paper'),
  ('.nm-conversion-form .nm-preset-btn', 'border', '#ffc107',
   'var(--alv-spice)', SPICE_FAM, 'a button outline on paper'),
  ('.nm-conversion-form .nm-preset-btn:hover', 'background', '#ffc107',
   'var(--alv-spice)', SPICE_FAM, 'FIXES 1.63 - white on hover'),
 ),
}

# The count badge's text moves with its fill, in the same rule.
INK_WITH_FILL = (
 ('ingredient_base_units_management.html',
  '.page-action-buttons .btn .action-count-badge.badge-unconvertible',
  'color', '#2c1810', 'var(--alv-on-accent)',
  'white on the warn solid is 5.38; #2c1810 on it would not read'),
)

# THE COOKBOOK THEME, COUNTED SO ITS SURVIVAL IS PROVED, NOT ASSUMED.
# #2c1810 IS A COOKBOOK BROWN TOO. It was left out of this tuple
# because the round meets it as the ink of a count badge on the
# ingredient page, and the suite's own check for stale literals is
# what found the other five - .book-recipe-card-title and friends.
# A theme counted by the colours I happened to notice is not a
# counted theme.
BOOK = ('#5c3a2a', '#f5e6d0', '#e8d9c0', '#8a6545', '#2c1810')
BOOK_PAGE = 'recipe_management.html'
EXPECT_BOOK = 22


BASE_ANCHOR = ("        --alv-warn-line:  #ecd39e;   "
               "/* the tint's own edge              */\n")

BASE_ADD = """        --alv-warn-line:  #ecd39e;   /* the tint's own edge              */

        /* RC-2, 9 Oct 2026 - the recipe module's warm identity.
           NOT --alv-warn, which means caution: these carry an Edit
           button, a Save button and a unit chip. --alv-warn would
           hold white at 5.38 and was refused on meaning, not ratio.
           --alv-spice SHARES --alv-grade-4's value deliberately.
           Ten candidates were measured: every orange light enough to
           read as orange rather than brown falls under 5.0 against
           white, and every one clearing 5.2 lands on this colour.
           Orange at the ratio this house holds its solids to IS
           burnt sienna, so the two tokens share a value on purpose
           and a later change to one must not be copied to the other. */
        --alv-spice:      #a8481a;   /* white on it - measures 5.82      */
        --alv-spice-ink:  #8a3f08;   /* text, and the hover partner 7.51 */
        --alv-spice-soft: #fdf0e4;   /* the tint - 6.71 with spice-ink   */
        --alv-spice-line: #f0d7bd;   /* edges, and pale warm on dark ink */
"""


def repoint_standards(base_text):
    """base.html's own standards block states how many design tokens it
    declares, and test_standards_doc checks the claim against reality.

    THIS ROUND ADDS FOUR, SO IT OWNS THAT NUMBER. It did not, first
    time: RC-2 re-pointed test_pair_contrast and test_amber and left
    this one, and the push stopped at 109 of 314 with

        FAIL base declares the 80 tokens the block says
             84 declared

    The reason it was missed is worth keeping. alv_impact.select()
    returned 296 suites for this round and I ran a subset of 36 chosen
    BY TOPIC - colour suites and recipe suites - which is a sweep over
    the suites I expected to be affected rather than over the ones the
    instrument said were. test_standards_doc is neither a colour suite
    nor a recipe suite; it is a suite about base, and this round
    changes base.

    COUNTED THE WAY THE SUITE COUNTS. A number derived by a different
    method from the one that checks it is a number that will disagree
    sooner or later - and note the suite does NOT strip comments before
    matching, so a token name followed by a colon inside a comment
    would count. Measuring rather than reasoning is the point.
    """
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', base_text, re.S))
    n = len(set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', css)))
    said = re.search(r'(\d+) design tokens', base_text)
    if not said:
        raise SystemExit('RC-2: base.html does not state a token count')
    if int(said.group(1)) == n:
        return base_text, n, n
    was = int(said.group(1))
    out = (base_text[:said.start(1)] + str(n)
           + base_text[said.end(1):])
    return out, was, n


def sites(code):
    """[(start, end, selector, property, literal)] for every colour
    literal in a rule body, found with the instrument that measured
    them - not with a regex over the file."""
    out = []
    for a, b in R.style_spans(code):
        seen = set()
        for sel, ba, bb, _ra, _rb in R.rule_spans(code, a, b):
            if (ba, bb) in seen:
                continue
            seen.add((ba, bb))
            pos = ba
            for chunk in code[ba:bb].split(';'):
                start = pos
                pos += len(chunk) + 1
                if ':' not in chunk or '{' in chunk or '}' in chunk:
                    continue
                prop, val = chunk.split(':', 1)
                voff = start + len(prop) + 1
                for s, e, lit in R.colour_spans(val):
                    out.append((voff + s, voff + e,
                                sel.split(' && ')[-1].strip(),
                                prop.strip().lower(), lit.lower()))
    return sorted(out)


def plan_page(page, code):
    """[(start, end, new)] plus the audit rows, or raise."""
    want = collections.Counter()
    for sel, prop, lit, new, fam, why in MAP.get(page, ()):
        want[(sel, prop, lit)] += 1
    for pg, sel, prop, lit, new, why in INK_WITH_FILL:
        if pg == page:
            want[(sel, prop, lit)] += 1

    found = collections.Counter()
    edits = []
    for s, e, sel, prop, lit in sites(code):
        key = (sel, prop, lit)
        if key not in want:
            continue
        found[key] += 1
        new = None
        for msel, mprop, mlit, mnew, _f, _w in MAP.get(page, ()):
            if (msel, mprop, mlit) == key:
                new = mnew
        if new is None:
            for pg, isel, iprop, ilit, inew, _w in INK_WITH_FILL:
                if pg == page and (isel, iprop, ilit) == key:
                    new = inew
        edits.append((s, e, new))

    if found != want:
        miss = [k for k in want if found[k] != want[k]]
        raise SystemExit(
            'RC-2: %s - the map and the page disagree on %d site(s). '
            'A map built against a tree that has since moved is a map '
            'of nothing, and this round refuses rather than do part '
            'of itself:\n%s'
            % (page, len(miss),
               '\n'.join('    wanted %d, found %d  %s %s %s'
                         % (want[k], found[k], k[0], k[1], k[2])
                         for k in miss)))
    return sorted(edits, reverse=True)


def apply_edits(code, edits):
    for s, e, new in edits:          # back to front, offsets stay valid
        code = code[:s] + new + code[e:]
    return code


def book_count(code):
    n = 0
    for _s, _e, _sel, _prop, lit in sites(code):
        if lit in BOOK:
            n += 1
    return n


def repoint_pair_census(live, dead, n, planned, C):
    """test_pair_contrast.py counts pairs, and this round changes the
    count. A ROUND THAT CHANGES A NUMBER OWNS EVERY NUMBER THAT COUNTS
    IT - derived here from the census over the PLANNED tree, never
    pinned by hand."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'test_pair_contrast.py')
    txt = read(p)
    out = txt

    rows = '\n'.join(
        "    (%r, %r, %.2f, %r)," % (r[0].replace(os.sep, '/'), r[1], r[2],
                                     kind_of(r, C))
        for r in live)
    old = re.search(r'LIVE = \(\n.*?\n\)\n', out, re.S)
    if not old:
        raise SystemExit('RC-2: cannot find the LIVE tuple in the pair census')
    out = out[:old.start()] + 'LIVE = (\n' + rows + '\n)\n' + out[old.end():]

    for pat, new in (
        (r'EXPECT_PAIRS = \d+', 'EXPECT_PAIRS = %d' % n),
    ):
        if len(re.findall(pat, out)) != 1:
            raise SystemExit('RC-2: %r is not in the pair census exactly '
                             'once' % pat)
        out = re.sub(pat, new, out)

    house = [r for r in live if kind_of(r, C) == 'house']
    band = [r for r in house if 4.0 <= r[2] < 4.5]
    bright = [r for r in live if kind_of(r, C) == 'bright']
    for pat, new in (
        (r"ok\(len\(band\) == \d+,", 'ok(len(band) == %d,' % len(band)),
        (r"ok\(len\(house\) == \d+,", 'ok(len(house) == %d,' % len(house)),
        (r"ok\(len\(bright\) >= \d+,", 'ok(len(bright) >= %d,'
         % max(len(bright), 0)),
    ):
        if len(re.findall(pat, out)) != 1:
            raise SystemExit('RC-2: %r is not in the pair census exactly '
                             'once' % pat)
        out = re.sub(pat, new, out)

    # THE PINS SECTION 5 HOLDS. Four of the seven pairs under 2:1 were
    # Bootstrap yellow under white text and this round takes them, so
    # the pinned floor moves with them or the suite fails for being out
    # of date rather than for a fault.
    sub2 = [r for r in live if r[2] < 2.0]
    worst = [r for r in sub2 if kind_of(r, C) == 'house']
    for pat, new in (
        (r'ok\(len\(sub2\) >= \d+,', 'ok(len(sub2) >= %d,' % len(sub2)),
        (r'ok\(len\(worst\) == \d+,', 'ok(len(worst) == %d,' % len(worst)),
    ):
        if len(re.findall(pat, out)) != 1:
            raise SystemExit('RC-2: %r is not in the pair census exactly '
                             'once' % pat)
        out = re.sub(pat, new, out)

    # AND THE PROSE, WHICH IS ALSO A NUMBER. The docstring names the
    # total and its three groups, and the footer repeats the total. A
    # round that moved 32 to 23 and left the words saying 32 has left a
    # false statement in the file that no gate would ever catch -
    # derived here, not hand-edited.
    stray = [r for r in live if kind_of(r, C) == 'stray']
    out = _prose(out, len(live), len(house), len(bright), len(stray),
                 len(sub2))

    if out == txt:
        raise SystemExit('RC-2: the pair census came back unchanged, which '
                         'cannot be true when ten pairs move')
    if not CHECK:
        backup(p)
        write(p, out)
    return len(live), len(dead), n


def _prose(out, ntot, nhouse, nbright, nstray, nsub2):
    """Re-point the counts the census states in words."""
    import re as _re
    a = out.index('AND THE 32 ARE NOT ANONYMOUS DEBT')
    a = out.rindex('=====', 0, a)
    b = out.index('NOT PROVED HERE: that any of the', a)
    block = (
        "=====================================================================\n"
        "AND THE %d ARE NOT ANONYMOUS DEBT\n"
        "=====================================================================\n"
        "\n"
        "   %2d  HOUSE TOKEN ON HOUSE TOKEN. EIGHTEEN are --alv-accent on an\n"
        "       --alv-accent-soft / --alv-line-soft / --alv-surface-deep\n"
        "       ground, 4.14 to 4.42 - the house pairing its own accent with\n"
        "       its own tint and missing AA by a tenth. That is ONE BASE\n"
        "       DECISION, not eighteen page fixes. --alv-accent-ink on\n"
        "       --alv-accent-soft reads 6.53:1.\n"
        "\n"
        "       THREE OF THE EIGHTEEN WERE ADDED BY AD-1, 8 Oct 2026, AND IT\n"
        "       DID NOT CREATE THEM. The tabs on admin_apms and personal are\n"
        "       written in page-local :root tokens and this census resolved\n"
        "       var() against base alone, so not one tab rule in the tree was\n"
        "       being counted. AD-1 taught it to read the page's own :root and\n"
        "       701 pairs became 714. They were always there.\n"
        "\n"
        "       TWO OF THE %d ARE NOT A TENTH. base's .icon-cancel:hover\n"
        "       is --alv-ink-strong on --alv-neutral at 1.49:1 and\n"
        "       .fi-ibadge is --alv-accent-ink on --alv-accent at 1.51:1.\n"
        "       Those are not low contrast, they are invisible text, and\n"
        "       section 5 says so separately so they cannot hide inside a\n"
        "       count of %d.\n"
        "\n"
        "   %2d  Bootstrap brights under white, plus the recipe oranges.\n"
        "       Decision 4 / round B-7. RC-2 took the recipe module's share\n"
        "       on 9 Oct 2026: forty-three declarations on five pages, sorted\n"
        "       into --alv-spice where warm is that module's identity and\n"
        "       --alv-warn where the rule's own ground already said warn.\n"
        "       Nine of these pairs rose above AA with it, four of them from\n"
        "       under 2:1.\n"
        "\n"
        "   %2d  one-offs with no family: #ccc on white, #adb5bd on\n"
        "       --alv-surface twice, and the accent on a lilac tint.\n"
        "\n"
        % (ntot, nhouse, nhouse, nhouse, nbright, nstray))
    out = out[:a] + block + out[b:]
    out = _re.sub(r'that any of the \d+ should be fixed',
                  'that any of the %d should be fixed' % ntot, out)
    out = _re.sub(r"print\('  NOT PROVED HERE: that any of the \d+ should be fixed",
                  "print('  NOT PROVED HERE: that any of the %d should be fixed"
                  % ntot, out)
    out = _re.sub(r"head\('5\. TWO OF THE \d+ ARE NOT A TENTH SHORT'\)",
                  "head('5. TWO OF THE %d ARE NOT A TENTH SHORT')" % nhouse,
                  out)
    return out


def kind_of(row, C):
    """house / bright / stray, the tags B-4b's census uses."""
    bg, ink = row[3], row[4]
    BRIGHTS = ('#ffc107', '#fd7e14', '#28a745', '#dc3545', '#007bff',
               '#20c997', '#e83e8c', '#6f42c1', '#17a2b8', '#1976d2',
               '#1565c0', '#e65100', '#f57c00', '#e8590c', '#d04e0a')
    if bg in BRIGHTS or ink in BRIGHTS:
        return 'bright'
    base = C.base_tokens(base_code=read(T.path_of('base.html')))
    vals = set(v.lower() for v in base.values() if str(v).startswith('#'))
    if bg in vals and ink in vals:
        return 'house'
    return 'stray'


def register():
    root = os.path.dirname(os.path.abspath(__file__))
    rp = os.path.join(root, 'alv_rounds.py')
    rt = read(rp)
    if "'%s'" % SUFFIX not in rt:
        m = list(re.finditer(r"^ROUNDS = \[", rt, re.M))
        if len(m) != 1:
            raise SystemExit('RC-2: ROUNDS is not declared exactly once')
        # THE LAST ENTRY, NOT THE FIRST BRACKET. as_left_by walks this
        # list in order, so a suffix inserted anywhere but the end
        # would make every round after it read the wrong backup.
        tail = "    '.bak_issuepanel',\n]\n"
        if rt.count(tail) != 1:
            raise SystemExit('RC-2: the tail of ROUNDS is not where this '
                             'round was measured - HM-2 must be applied '
                             'first and must still be last')
        ins = ("    '.bak_issuepanel',\n"
               "    # RC-2, 9 Oct 2026 - the recipe module's warm literals\n"
               "    # sorted into the two families their own grounds declare.\n"
               "    '%s',\n]\n" % SUFFIX)
        rt2 = rt.replace(tail, ins, 1)
        if not CHECK:
            backup(rp)
            write(rp, rt2)
    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        anc = "    'test_pair_contrast.py',\n"
        if pt.count(anc) != 1:
            raise SystemExit("RC-2: the $suites anchor is not in %s exactly "
                             "once - it has moved" % PS1)
        pt2 = pt.replace(anc, anc + "    '%s',\n" % SUITE, 1)
        if not CHECK:
            backup(pp)
            write(pp, pt2)
    return 2


PAGE_NOTE = """<style>
    /* RC-2, 9 Oct 2026 - this page's warm literals were sorted into
       the two families its own rules already declared: --alv-spice
       where warm is this module's identity (an Edit button, a Save
       button, a unit chip, the conversion controls) and --alv-warn
       where the rule's own ground was already a warn tint. The
       cookbook browns on recipe_management are deliberate and were
       left alone - see apply_recipe_spice.py for the list and the
       reasons. */"""


def add_note(code):
    """Stamp the round's note into the page's first <style> block.

    WITHOUT THIS THE ROUND IS NOT IDEMPOTENT. The first version marked
    only base.html, so a second run found its own converted pages,
    could not match a single literal, and refused the whole round -
    correctly, but for the wrong reason. A patcher has to be able to
    recognise its own work.
    """
    m = re.search(r'<style[^>]*>', code)
    if not m:
        raise SystemExit('RC-2: no <style> block to stamp')
    return code[:m.start()] + PAGE_NOTE + code[m.end():]


# ---------------------------------------------------------------------
# B-4's LEAVE LIST, AMENDED BY THE ROUND THAT TOOK PART OF IT.
#
# apply_amber.LEAVE pins #fd7e14 with the reason "orange, hue 27 -
# decision 4, the Bootstrap brights", and test_amber asserts the count
# in the tree still matches what B-4 left. RC-2 takes four of those
# six, so that assertion is now false for a good reason - and a suite
# failing because a later round did its job is a suite owed an update,
# not a round owed a revert.
#
# THIS IS NOT THE SAME AS THE HIGHLIGHTER. B-4 also pinned
# .spell-error-context .highlight-word in LEAVE_RULES with the reason
# "brightness IS the function" - a spell-check marker pen. RC-2's
# first draft converted it anyway and test_amber caught that too. That
# one was a decision already taken and RC-2 reverted it rather than
# re-point the suite. A pinned COUNT moves when a later round owns
# part of it; a pinned DECISION does not move because a later round
# finds it inconvenient.
# ---------------------------------------------------------------------
AMBER_SUITE = 'test_amber.py'

AMBER_EDITS = (
    ("""for lit, why in sorted(B.LEAVE.items()):
    here = sum(T.code_only(read(p)).lower().count(lit) for p in T.templates())""",
     """# RC-2, 9 Oct 2026 - the share of B-4's leave list that a later
# round has taken, with the owner named. Subtracted from the live
# count so this section still asserts B-4's decision and not the
# tree's accidental total.
RC2_TOOK = {'#fd7e14': 4}

for lit, why in sorted(B.LEAVE.items()):
    here = sum(T.code_only(read(p)).lower().count(lit)
               for p in T.templates()) + RC2_TOOK.get(lit, 0)""",
     'the leave-list count'),
)


def repoint_amber():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), AMBER_SUITE)
    txt = read(p)
    if 'RC2_TOOK' in txt:
        return 0
    out = txt
    for old, new, what in AMBER_EDITS:
        if out.count(old) != 1:
            raise SystemExit('RC-2: %s - %s is not in %s exactly once '
                             '(found %d)' % (AMBER_SUITE, what, AMBER_SUITE,
                                             out.count(old)))
        out = out.replace(old, new, 1)
    if not CHECK:
        backup(p)
        write(p, out)
    return len(AMBER_EDITS)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    bt = read(T.path_of('base.html'))

    # THE ROUND THIS ONE BUILDS ON, TESTED WHERE IT ACTUALLY LANDED.
    # My first gate asked base.html for the string 'B-4b' and refused,
    # because B-4b never touches base - it owns the pair census. The
    # dependency is the census, so the gate reads the census.
    pc = os.path.join(root, 'test_pair_contrast.py')
    if not os.path.isfile(pc) or 'LIVE = (' not in read(pc):
        raise SystemExit('RC-2: test_pair_contrast.py is missing or has no '
                         'LIVE tuple - B-4b built the census this round '
                         're-points and it has to be there first')
    if "'.bak_editink'" not in read(os.path.join(root, 'alv_rounds.py')):
        raise SystemExit('RC-2: B-4b is not registered in alv_rounds.ROUNDS')

    done = MARK in bt
    pages = sorted(MAP)

    # ---- MEASURE, THEN WRITE. Build the whole planned tree first ----
    planned = {}
    edits_by_page = {}
    for page in pages:
        p = T.path_of(page)
        raw = read(p)
        if MARK in raw:
            done = True
            continue
        code = T.code_only(raw)      # length-preserving, so offsets carry
        edits = plan_page(page, code)
        edits_by_page[page] = (p, raw, edits)
        planned[p] = add_note(apply_edits(raw, edits))

    if done and not edits_by_page:
        print('RC-2  already applied')
        return 0

    # the cookbook theme must be exactly as many after as before
    bp = T.path_of(BOOK_PAGE)
    before_book = book_count(T.code_only(read(bp)))
    after_book = book_count(T.code_only(planned.get(bp, read(bp))))
    if before_book != EXPECT_BOOK or after_book != EXPECT_BOOK:
        raise SystemExit(
            'RC-2: the cookbook theme measures %d before and %d after, and '
            'the round was written against %d. Those browns are a '
            'deliberate sub-theme and this round does not touch one of '
            'them' % (before_book, after_book, EXPECT_BOOK))

    # base.html gains the family
    if MARK not in bt:
        if bt.count(BASE_ANCHOR) != 1:
            raise SystemExit('RC-2: the base token anchor is not in '
                             'base.html exactly once')
        nb = bt.replace(BASE_ANCHOR, BASE_ADD, 1)
        nb, tok_was, tok_now = repoint_standards(nb)
        planned[T.path_of('base.html')] = nb
    else:
        tok_was = tok_now = None

    # ---- THE CENSUS IS FIXED FIRST, THEN IT JUDGES ----
    nfix, census_src = fix_census()
    C = census_module(census_src)
    n0, live0, dead0 = C.census()
    n1, live1, dead1 = C.census(override=planned)

    was = {(r[0].replace(os.sep, '/'), r[1]): r[2] for r in live0}
    now = {(r[0].replace(os.sep, '/'), r[1]): r[2] for r in live1}
    worse = [(k, was[k], now[k]) for k in was
             if k in now and now[k] < was[k] - 0.005]
    newly = [(k, now[k]) for k in now if k not in was]
    fixed = [(k, was[k]) for k in was if k not in now]

    if worse:
        raise SystemExit(
            'RC-2: %d pair(s) read WORSE after this round. A colour round '
            'that lowers a ratio has to say so in its own text or not '
            'happen:\n%s' % (len(worse), '\n'.join(
                '    %s %s  %.2f -> %.2f' % (k[0], k[1], a, b)
                for k, a, b in worse)))
    if newly:
        raise SystemExit(
            'RC-2: %d pair(s) fall BELOW AA that did not before:\n%s'
            % (len(newly), '\n'.join('    %s %s  %.2f' % (k[0], k[1], v)
                                     for k, v in newly)))

    recipe_fixed = [f for f in fixed if any(
        w in f[0][0] for w in ('recipe', 'ingredient', 'meal',
                               'unit_conversion'))]
    if len(recipe_fixed) != 9:
        raise SystemExit(
            'RC-2: the census says %d recipe pair(s) rise above AA and the '
            'round was measured at 9. The tenth site - '
            '.ai-suggestion-type-icon.reduce - is invisible to the census '
            'by construction and is not counted here:\n%s'
            % (len(recipe_fixed), '\n'.join(
                '    %s %s  was %.2f' % (k[0], k[1], v)
                for k, v in recipe_fixed)))

    # ---- NOW WRITE ----
    nspice = sum(1 for v in MAP.values() for e in v if e[4] == SPICE_FAM)
    nwarn = sum(1 for v in MAP.values() for e in v if e[4] == WARN_FAM)
    ntot = sum(len(v) for v in MAP.values()) + len(INK_WITH_FILL)

    if not CHECK:
        for page, (p, raw, edits) in edits_by_page.items():
            backup(p)
            write(p, planned[p] + '')
        bpath = T.path_of('base.html')
        if bpath in planned:
            backup(bpath)
            write(bpath, planned[bpath])

    nlive, ndead, npairs = repoint_pair_census(live1, dead1, n1, planned, C)
    namber = repoint_amber()
    nreg = register()

    print('')
    print('RC-2  %d declaration(s) on %d page(s): %d spice, %d warn'
          % (ntot, len(MAP), nspice, nwarn))
    print('RC-2  4 token(s) added to base - spice shares grade-4 on purpose')
    if tok_was is not None:
        print('RC-2  standards block re-pointed %d -> %d design tokens - '
              'base states' % (tok_was, tok_now))
        print('RC-2  its own count and test_standards_doc checks the claim')
    print('RC-2  cookbook theme %d before, %d after - untouched'
          % (before_book, after_book))
    print('RC-2  pair census %d -> %d pairs, %d -> %d live below AA'
          % (n0, n1, len(live0), len(live1)))
    print('RC-2  %d pair(s) rise above AA, 0 fall, 0 read worse'
          % len(fixed))
    print('RC-2  and a tenth the census cannot pair: '
          '.ai-suggestion-type-icon.reduce, white from the base selector')
    print('RC-2  census blind spot fixed: %d edit(s) to %s - a round '
          'adding a' % (nfix, CENSUS))
    print('RC-2  token was measured against the base.html on disk, so '
          'every pair it')
    print('RC-2  converted LEFT the census instead of being judged')
    print('RC-2  test_amber re-pointed: %d edit(s) - four of B-4\'s six '
          '#fd7e14 are' % namber)
    print('RC-2  this round\'s now. Its PINNED DECISION on the spell-check '
          'marker pen')
    print('RC-2  was reverted instead, not re-pointed')
    print('RC-2  %d registry file(s) resolved' % nreg)
    print('RC-2  applied' if CHECK else 'RC-2  ok')
    return 0



# ---------------------------------------------------------------------
# THE CENSUS'S OWN BLIND SPOT, FIXED BY THE ROUND THAT FOUND IT.
#
# apply_edit_ink.base_tokens() read base.html off the DISK even when
# census() had been handed an override to measure a tree not yet
# written. A pair converted to a token base did not yet carry resolved
# to None, and pair_table drops what it cannot resolve - so the pair
# left the census silently instead of being judged.
#
# RC-2's first gate reported "713 -> 706 pairs, 9 rise above AA, 0
# read worse" while measuring none of the 43 declarations it converts.
# Nothing got worse because nothing was looked at. The pair count
# falling by seven was the only visible symptom, and a round that only
# ever adds tokens could have shipped on a gate that proved nothing.
#
# Every colour round introducing a token has had that same vacuous
# gate. RC-2 is the first since the census was built to add one.
# ---------------------------------------------------------------------
CENSUS = 'apply_edit_ink.py'

CENSUS_EDITS = (
    ("def base_tokens(code=None):",
     "def base_tokens(code=None, base_code=None):",
     'the signature'),

    ("""    A page token that resolves to another token is chased by resolve(),
    so --alivente-dark: var(--alv-accent) lands on #0e7c8b.
    \"\"\"
    out = {}
    srcs = [T.code_only(read(T.path_of('base.html')))]""",
     """    A page token that resolves to another token is chased by resolve(),
    so --alivente-dark: var(--alv-accent) lands on #0e7c8b.

    RC-2, 9 Oct 2026: `base_code` IS NOT OPTIONAL DECORATION. This used
    to read base.html off the DISK unconditionally, including when
    census() was handed an override to measure a tree that had not been
    written yet. Any pair a round converted to a token base did not yet
    carry resolved to None, and pair_table drops a pair it cannot
    resolve - so the pair did not get worse, did not get better, it
    SILENTLY LEFT THE CENSUS. RC-2 converts 42 declarations to a family
    it adds in the same round, and its first gate reported nine pairs
    rising above AA and nothing getting worse while measuring none of
    them. Every colour round that introduces a token has had that same
    vacuous gate; RC-2 is the first since this census was built to add
    one, so it is the first to hit it.
    \"\"\"
    out = {}
    bt = base_code if base_code is not None else read(T.path_of('base.html'))
    srcs = [T.code_only(bt)]""",
     'the token source'),

    ("""    override = override or {}
    n = 0
    live, dead = [], []
    for p in sorted(T.templates()):
        code = T.code_only(override.get(p) or read(p))
        # AD-1: the page's OWN :root as well as base's, or every rule
        # written in a page-local token goes uncounted.
        for sel, (bg, ink) in pair_table(code, base_tokens(code)).items():""",
     """    override = override or {}
    n = 0
    live, dead = [], []
    # RC-2: base as the OVERRIDE leaves it, so a round adding a token
    # is measured against the base.html it is about to write and not
    # against the one on disk. Without this every converted pair
    # resolves to None and leaves the census instead of being judged.
    bpath = T.path_of('base.html')
    base_code = override.get(bpath) or read(bpath)
    for p in sorted(T.templates()):
        code = T.code_only(override.get(p) or read(p))
        # AD-1: the page's OWN :root as well as base's, or every rule
        # written in a page-local token goes uncounted.
        for sel, (bg, ink) in pair_table(
                code, base_tokens(code, base_code)).items():""",
     'the census call'),
)


def fix_census():
    """Apply CENSUS_EDITS, then reload the module so THIS run measures
    with the fixed instrument. A round that fixes its own measuring
    stick and then measures with the old one has fixed nothing."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), CENSUS)
    txt = read(p)
    if 'base_code' in txt:
        return 0, txt
    out = txt
    for old, new, what in CENSUS_EDITS:
        if out.count(old) != 1:
            raise SystemExit('RC-2: %s - %s is not in the census exactly '
                             'once (found %d). The anchor holds what the '
                             'FILE holds, and this one no longer does'
                             % (CENSUS, what, out.count(old)))
        out = out.replace(old, new, 1)
    if not CHECK:
        backup(p)
        write(p, out)
    return len(CENSUS_EDITS), out


def census_module(src):
    """The census as THIS round leaves it, as a live module.

    --check must measure with the fixed instrument too, or the dry run
    proves something the real run does not. Loading from source rather
    than importing means the measurement does not depend on whether
    the file has been written yet."""
    import importlib.util as _u
    root = os.path.dirname(os.path.abspath(__file__))
    spec = _u.spec_from_loader('alv_census_rc2', loader=None)
    mod = _u.module_from_spec(spec)
    mod.__file__ = os.path.join(root, CENSUS)
    mod.__dict__['__name__'] = 'alv_census_rc2'
    exec(compile(src, mod.__file__, 'exec'), mod.__dict__)
    return mod

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
