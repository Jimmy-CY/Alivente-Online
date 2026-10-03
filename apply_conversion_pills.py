# -*- coding: utf-8 -*-
"""SECTION UC, ROUND UC-1 - THE UNIT CONVERSIONS PILLS

Demetri, with a screenshot: "Can we mellow down the green colour for qty and
the yellow colour for Applies To. Do we have any standards??"

Yes, and it is already the mellow one. base has .alv-pill with five tones -
soft ground, strong ink, soft border - and this page uses NONE of them. It
paints four colours of its own, two of them as gradients.

Agreed, 2 Oct: onto the house pill scale.

==========================================================================
A SCOPE IS NOT A VERDICT
==========================================================================
The Applies To column says WHICH CONVERSIONS A ROW GOVERNS. It is amber for
one answer and green for the other, and neither is a judgement about
anything:

    before   Specific ingredient   #ffc107 amber on black
             Generic (All)         #28a745 green on white
    after    Specific ingredient   .alv-pill-info      (keeps the star)
             Generic (All)         .alv-pill-neutral   (keeps the globe)

Green reads as GOOD and amber reads as NEEDS ATTENTION. A conversion that
applies to one ingredient is not in better or worse health than one that
applies to all of them - so the tones that carry a verdict are the wrong
ones, and the same distinction settles the quantity chips: a number is
information, so it is info.

    before   both numbers   a green-to-teal gradient, white, box-shadow
    after    both numbers   .alv-pill .alv-pill-info

==========================================================================
AND A RULE THAT HAS NEVER ONCE FIRED
==========================================================================
    .conversion-number:last-of-type {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);

Written to paint the SECOND number blue. It has never done it, and the
screenshot is the proof: both numbers are the same green.

:last-of-type matches the last element OF ITS TYPE among its siblings, and
the siblings are

    span.conversion-number   span.conversion-unit   span.conversion-arrow
    span.conversion-number   span.conversion-unit

- five SPANS. The last span is a .conversion-unit, which carries no
.conversion-number class, so the selector matches nothing. The author
wanted :last-child of a class, which CSS has no way to express.

The round does not resurrect it. Two numbers in one row say "1 cup" and
"240 grams"; they are the same KIND of thing and painting one of them a
different colour was decoration, not information. The rule goes, and the
gate asserts it never applied in the first place rather than merely that it
is gone - because "we removed a rule" and "we removed a rule that did
nothing" are different claims and only the second one is safe.

Same shape as C-1's two dead rules and F3's .conversion-number note.

Backups: .bak_convpills. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_convpills'
ROOT = os.getcwd()
CRLF = {}

TPL = os.path.join(ROOT, 'pages', 'templates',
                   'unit_conversions_management.html')


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
            raise SystemExit('UC1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('UC1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def code_only(t):
    """Comments blanked in all three syntaxes, length preserved. IB-1's
    lesson, four hours old: a template carries Django, HTML and CSS
    comments, and an instrument that strips two of the three can still read
    its own prose as the defect."""
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


print('=' * 74)
print('SECTION UC, ROUND UC-1 - THE CONVERSION PILLS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TPL)
BEFORE = code_only(t)

# ==========================================================================
# 0. THE DEAD RULE, PROVED DEAD BEFORE IT IS REMOVED.
#
# A selector that has never matched is a different thing from one that has,
# and only the first can be deleted without changing a pixel. Proved from
# the MARKUP, by walking the siblings the way a browser does.
# ==========================================================================
disp = re.search(r'<div class="conversion-display">(.*?)</div>', BEFORE, re.S)
if not disp:
    raise SystemExit('UC1: the conversion display is not where this round '
                     'thinks')
sibs = re.findall(r'<span class="([^"]+)"', disp.group(1))
if len(sibs) != 5:
    raise SystemExit('UC1: the display holds %d spans, not the 5 this round '
                     'reasons about: %s' % (len(sibs), sibs))
# :last-of-type picks the last SPAN, whatever class it carries.
if 'conversion-number' in sibs[-1].split():
    raise SystemExit('UC1: the last span IS a .conversion-number - the rule '
                     'DOES fire and removing it would change the screen')
print('  the five spans are: %s' % ' '.join(s.split()[0] for s in sibs))
print('  the last one is .%s, so :last-of-type never selected a number'
      % sibs[-1].split()[0])

# ==========================================================================
# 1. THE QUANTITY CHIPS.
# ==========================================================================
OLD_NUM = """.conversion-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    padding: 8px 14px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 16px;
    min-width: 45px;
    box-shadow: 0 2px 6px rgba(40, 167, 69, 0.3);
}

.conversion-number:last-of-type {
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    box-shadow: 0 2px 6px rgba(0, 123, 255, 0.3);
}
"""

NEW_NUM = """/* THE QUANTITY CHIPS - UC-1, 2 Oct 2026.
   Demetri: "Can we mellow down the green colour for qty... Do we have any
   standards??" base has had five pill tones since the contrast work, and
   this page used none of them.

   INFO, NOT GOOD. A quantity is information; green means healthy, and a
   multiplier is not in good health. The same distinction decides the
   Applies To column below - a scope is not a verdict.

   AND THE BLUE RULE THAT NEVER FIRED IS GONE. It read

       .conversion-number:last-of-type { background: ...blue... }

   and was written to paint the SECOND number. :last-of-type matches the
   last element of its type among its siblings, and the siblings are five
   SPANS ending in a .conversion-unit - so it never selected a number at
   all. That is why both numbers rendered the same green in the screenshot.
   The round does not resurrect it: two numbers in one row are the same
   KIND of thing, and colouring one of them differently was decoration.

   Only the size is kept local. .alv-pill is 12px, and these are read as
   values rather than as labels.                   [test_conversion_pills] */
.conversion-number {
    font-size: 15px;
    padding: 5px 12px;
    min-width: 45px;
    justify-content: center;
}
"""

t = swap(t, OLD_NUM, NEW_NUM, 'the .conversion-number rules', TPL)

OLD_SPANS = """                            <span class="conversion-number">1</span>
                            <span class="conversion-unit">{{ conversion.from_unit.name }}</span>
                            <span class="conversion-arrow">→</span>
                            <span class="conversion-number">{{ conversion.multiplier|normalize_decimal }}</span>
                            <span class="conversion-unit">{{ conversion.to_unit.name }}</span>
"""

NEW_SPANS = """                            <span class="alv-pill alv-pill-info conversion-number">1</span>
                            <span class="conversion-unit">{{ conversion.from_unit.name }}</span>
                            <span class="conversion-arrow">→</span>
                            <span class="alv-pill alv-pill-info conversion-number">{{ conversion.multiplier|normalize_decimal }}</span>
                            <span class="conversion-unit">{{ conversion.to_unit.name }}</span>
"""

t = swap(t, OLD_SPANS, NEW_SPANS, 'the two quantity chips', TPL)

# ==========================================================================
# 2. THE ARROW. It took its green from the same place the chips did.
# ==========================================================================
t = swap(t, """.conversion-arrow {
    color: #28a745;""", """.conversion-arrow {
    /* UC-1: the arrow took its green from the chips it sits between.
       It is punctuation, so it reads as soft ink rather than as a tone. */
    color: var(--alv-ink-faint);""", 'the arrow colour', TPL)

# ==========================================================================
# 3. APPLIES TO. Four inline declarations, gone.
# ==========================================================================
OLD_APPLIES = """                        {% if conversion.specific_ingredient %}
                            <span style="background: #ffc107; color: #000; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 500;">
                                <i class="fas fa-star"></i> {{ conversion.specific_ingredient.name }}
                            </span>
                        {% else %}
                            <span style="background: #28a745; color: white; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 500;">
                                <i class="fas fa-globe"></i> Generic (All)
                            </span>
                        {% endif %}
"""

NEW_APPLIES = """                        {# A SCOPE IS NOT A VERDICT - UC-1, 2 Oct 2026. This column   #}
                        {# says which conversions a row governs. It was amber for one #}
                        {# answer and green for the other, and neither is a judgement #}
                        {# - a conversion that applies to one ingredient is not in    #}
                        {# better or worse health than one that applies to all. So    #}
                        {# info for the narrower scope, neutral for the wider one,    #}
                        {# and the two icons stay exactly as they were.               #}
                        {% if conversion.specific_ingredient %}
                            <span class="alv-pill alv-pill-info">
                                <i class="fas fa-star"></i> {{ conversion.specific_ingredient.name }}
                            </span>
                        {% else %}
                            <span class="alv-pill alv-pill-neutral">
                                <i class="fas fa-globe"></i> Generic (All)
                            </span>
                        {% endif %}
"""

t = swap(t, OLD_APPLIES, NEW_APPLIES, 'the Applies To pair', TPL)

# ==========================================================================
# 4. THE SAME TWO COLOURS, IN THE MODAL THIS PAGE OPENS.
#
# The conversions-needed modal asks the same question the Applies To column
# answers - Generic or Specific - and painted it with the SAME #28a745 and
# #ffc107. Mellowing the column and leaving the chooser that sets it in the
# old pair would have been half a round: the two would disagree about what
# the distinction looks like, on one screen, seconds apart.
#
# base's .alv-choice is the house radio card, but it is display: block with
# a left rail and these sit in a two-column grid. So the LAYOUT is left
# alone and only the paint moves - onto two local classes, which is six
# inline declarations fewer than before.
#
# AND THE EMPHASIS FOLLOWS THE COLUMN, NOT THE OLD CARD. Generic was the
# green one and so read as the approved answer; it is the WIDER scope, and
# the column now paints it neutral. Specific takes the accent in both
# places.
# ==========================================================================
t = swap(t, """.conversion-unit {\n    color: #495057;""", """/* THE SCOPE CHOOSER - UC-1, 2 Oct 2026. The modal asks the question the
   Applies To column answers, and painted it with the same two colours. The
   layout stays (a two-column grid, not .alv-choice's stacked rail); only
   the paint moves, onto the tokens the column's pills use. */
.uc-scope {
    display: flex;
    align-items: flex-start;
    padding: 12px 12px 12px 24px;
    border: 2px solid var(--alv-line);
    border-radius: 8px;
    background: var(--alv-paper);
    cursor: pointer;
}
.uc-scope-specific { border-color: var(--alv-accent-line); background: var(--alv-accent-soft); }
.uc-scope-specific .uc-scope-name { color: var(--alv-accent-ink); }
.uc-scope-generic  { border-color: var(--alv-line); background: var(--alv-neutral-soft); }
.uc-scope-generic .uc-scope-name { color: var(--alv-neutral); }
.uc-scope-name { font-weight: 600; }

.conversion-unit {
    color: #495057;""", 'the .conversion-unit rule as an anchor', TPL)

t = swap(t, """                            <label class="d-flex align-items-start" style="padding: 12px 12px 12px 24px; border: 2px solid #28a745; border-radius: 8px; background: #f0fff4; cursor: pointer;">""",
         """                            <label class="uc-scope uc-scope-generic">""",
         'the Generic card', TPL)
t = swap(t, """                                    <div style="font-weight: 600; color: #28a745;">
                                        <i class="fas fa-globe"></i> Generic""",
         """                                    <div class="uc-scope-name">
                                        <i class="fas fa-globe"></i> Generic""",
         'the Generic label', TPL)
t = swap(t, """                            <label class="d-flex align-items-start" style="padding: 12px 12px 12px 24px; border: 2px solid #ffc107; border-radius: 8px; background: #fffbf0; cursor: pointer;">""",
         """                            <label class="uc-scope uc-scope-specific">""",
         'the Specific card', TPL)
t = swap(t, """                                    <div style="font-weight: 600; color: #856404;">
                                        <i class="fas fa-star"></i> ${item.ingredient}""",
         """                                    <div class="uc-scope-name">
                                        <i class="fas fa-star"></i> ${item.ingredient}""",
         'the Specific label', TPL)

# ==========================================================================
# 5. THE PHONE OVERRIDE follows the chip it overrides.
# ==========================================================================
t = swap(t, """    .conversion-number {
        font-size: 14px;
        padding: 6px 10px;
        min-width: 38px;
    }""", """    .conversion-number {
        /* UC-1: one step down from the desktop size above, which is now
           .alv-pill's size plus this page's own two properties. */
        font-size: 13px;
        padding: 4px 9px;
        min-width: 38px;
    }""", 'the phone chip override', TPL)

if not CHECK:
    back_up(TPL, raw)
    write(TPL, t)
print('  unit_conversions_management.html   chips and Applies To onto the '
      'house pills')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
AFTER = code_only(read(TPL)[0])

# 1. THE FOUR INLINE DECLARATIONS AND BOTH GRADIENTS ARE GONE.
for dead, what in (('#ffc107', 'the amber'), ('#28a745', 'the green'),
                   ('#20c997', 'the teal half of the gradient'),
                   ('#007bff', 'the blue that never fired'),
                   ('#0056b3', 'its darker half'),
                   ('linear-gradient', 'the gradients')):
    n = AFTER.count(dead)
    b = BEFORE.count(dead)
    if n:
        raise SystemExit('UC1: %s survives %d time(s) (was %d)'
                         % (what, n, b))
print('  five literals and both gradients are gone (was %d occurrences)'
      % sum(BEFORE.count(x) for x in ('#ffc107', '#28a745', '#20c997',
                                      '#007bff', '#0056b3')))

# 2. NO INLINE background= SURVIVES IN THE TABLE BODY.
body = re.search(r'<tbody[^>]*>(.*?)</tbody>', AFTER, re.S)
if not body:
    raise SystemExit('UC1: no <tbody> to check')
inline = re.findall(r'style="[^"]*background[^"]*"', body.group(1))
if inline:
    raise SystemExit('UC1: %d inline background(s) left in the rows: %s'
                     % (len(inline), inline[:2]))
print('  and no row paints its own background any more')

# 3. THE PILLS ARE THE HOUSE ONES, IN THE RIGHT TONES.
for cls, n_want, what in (('alv-pill-info', 3, 'two chips and the scope'),
                          ('alv-pill-neutral', 1, 'the wider scope')):
    n = len(re.findall(r'\b%s\b' % cls, AFTER))
    if n != n_want:
        raise SystemExit('UC1: %s appears %d times, not %d - %s'
                         % (cls, n, n_want, what))
if 'alv-pill-good' in AFTER or 'alv-pill-attn' in AFTER:
    raise SystemExit('UC1: a verdict tone is back on a scope')
print('  three info pills and one neutral, and not one verdict tone')

# 4. THE ICONS SURVIVED. A round that mellowed the colour and lost the star
#    would have changed what the column MEANS.
for icon in ('fa-star', 'fa-globe'):
    if AFTER.count(icon) != BEFORE.count(icon):
        raise SystemExit('UC1: %s went from %d to %d'
                         % (icon, BEFORE.count(icon), AFTER.count(icon)))
print('  the star and the globe are exactly as many as before')

# 5. THE DEAD RULE IS GONE AND IS STILL PROVABLY DEAD. Re-asked of the
#    markup AFTER the write, because the round touched those very spans.
if ':last-of-type' in AFTER:
    raise SystemExit('UC1: a :last-of-type rule survives')
disp = re.search(r'<div class="conversion-display">(.*?)</div>', AFTER, re.S)
sibs = re.findall(r'<span class="([^"]+)"', disp.group(1))
if len(sibs) != 5 or 'conversion-number' in sibs[-1].split():
    raise SystemExit('UC1: the sibling run changed - the removal is no '
                     'longer provably invisible: %s' % sibs)
print('  the rule is gone, and the last of five spans is still a .%s'
      % sibs[-1].split()[0])

# 6. base REALLY DEFINES WHAT THIS PAGE NOW LEANS ON. A page that drops its
#    own paint and names a class base does not carry renders unstyled.
base = read(os.path.join(ROOT, 'pages', 'templates', 'base.html'))[0]
bcode = code_only(base)
for cls in ('.alv-pill', '.alv-pill-info', '.alv-pill-neutral'):
    if not re.search(re.escape(cls) + r'[\s,{]', bcode):
        raise SystemExit('UC1: base does not define %s' % cls)
print('  base defines .alv-pill, -info and -neutral, which is what the page '
      'now leans on')

# 7. NO NEW COLOUR ENTERED THE TREE.
hexes = lambda s: set(x.lower() for x in re.findall(r'#[0-9a-fA-F]{3,8}\b', s))
new = hexes(AFTER) - hexes(BEFORE)
if new:
    raise SystemExit('UC1: %d colour(s) this page did not have: %s'
                     % (len(new), sorted(new)))
print('  the page carries %d distinct colours, down from %d, and none new'
      % (len(hexes(AFTER)), len(hexes(BEFORE))))

# 8. THE MARKUP STILL CLOSES, AND THE COMMENTS ARE IN THE RIGHT PLACE AND
#    SHAPE - B-1b and B-1c, both of which reached Live.
raw_t = read(TPL)[0]
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', AFTER))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', AFTER))
    if a != z:
        raise SystemExit('UC1: %s %d vs %s %d' % (tag, a, close, z))
b2 = re.sub(r'<(script|style)\b.*?</\1>', '', AFTER, flags=re.S)
d = len(re.findall(r'<div\b', b2)) - len(re.findall(r'</div\s*>', b2))
if d:
    raise SystemExit('UC1: %+d unbalanced <div>' % d)
bad = [i for i, ln in enumerate(raw_t.split('\n'), 1)
       if '{#' in ln and '#}' not in ln]
if bad:
    raise SystemExit('UC1: a Django comment spans lines at %s - the lexer '
                     'has no DOTALL' % bad[:3])
OPENER, CLOSER = '<' + '!--', '--' + '>'
depth = 0
for mm in re.finditer(r'<[a-zA-Z/!]|>', raw_t):
    if mm.group(0) == '>':
        depth = max(0, depth - 1)
    elif raw_t.startswith(OPENER, mm.start()):
        if depth:
            raise SystemExit('UC1: a comment opens inside a tag at line %d'
                             % (raw_t.count('\n', 0, mm.start()) + 1))
    else:
        depth = 1
print('  every if, for and <div> closes, and no comment is misplaced')

print('-' * 74)
print('  A scope is not a verdict, and a rule that never fired is not a')
print('  rule you can say you removed from the screen.')
print('=' * 74)
