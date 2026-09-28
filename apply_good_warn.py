# -*- coding: utf-8 -*-
"""SECTION H, ROUND H7 - THE GREEN AND THE AMBER

base answers Bootstrap's INFO family and has since the accent round: put
`class="badge badge-info"` on a page and it comes out house teal, with no
page rule and no markup change. SUCCESS and WARNING were never answered,
so they still come straight off the CDN.

MEASURED, 28 Sep 2026, over the 120 templates
    114 uses of the two families across 35 files. Split by what they are:

        62  STATUS       alert-warning 16, alert-success 12,
                         badge-success 11, text-success 7, badge-warning 7,
                         bg-success 5, text-warning 3, bg-warning 1
        52  BUTTONS      btn-success 40, btn-warning 8,
                         btn-outline-success 4

    Bootstrap ships success #28a745 and warning #ffc107. On white they
    measure 3.13 and 1.63; on #e9ecef, which is what this system's panels
    and card heads are actually painted, 2.64 and 1.37.

    THE WORST OF IT IS NOT TEXT. Five card heads carry
    `bg-success text-white` and one carries `bg-warning text-white` -
    wcim_results.html heads its "Almost there" tier that way, white on
    #ffc107, 1.63. A heading you cannot read. Bootstrap's own
    .badge-warning is yellow with DARK ink for exactly this reason, which
    is why this round sets a colour on every fill it repaints rather than
    only the background.

WHAT THIS ROUND DOES
    The status families point at --alv-good and --alv-warn, which is what
    their names already claim. Fourteen rules in base, mirroring the
    INFO block line for line. No markup changes at all - and because the
    class is the same whether it was typed in a template or injected by
    script, the eleven alerts that pages build inside JS strings are
    covered by the same rules.

THE FOUR TOKENS
    An alert needs three values - a tint, an edge, an ink - and the good
    and warn families had two between them. So each gains the two steps
    the ACCENT family already has, and the shape of all three becomes the
    same: base, -ink, -soft, -line.

        --alv-good-ink   #155737   7.56 on good-soft, 8.57 on white
        --alv-good-line  #bfe0cd   the literal already in base, on
                                   .icon-save's border - named, not
                                   invented, and .icon-save now reads the
                                   name instead of repeating the hex
        --alv-warn-ink   #6a4a05   7.34 on warn-soft, 8.09 on white
        --alv-warn-line  #ecd39e   the amber family's only new colour;
                                   1.32 on its own tint, where the accent
                                   line sits at 1.36 on its own

    The inks are deeper than the accent's (6.53 on its tint) on purpose:
    Bootstrap's shipped .alert-success already measures 6.99, and this
    round is not allowed to make anything worse than what it replaces.

WHAT MOVES, AND BY HOW MUCH
                                    before   after
        bg-warning + text-white       1.63    5.38
        text-warning on white         1.63    5.38
        text-warning on #e9ecef       1.37    4.54
        badge-warning as white ink    1.94    5.38
        bg-success + text-white       3.13    5.12
        text-success on white         3.13    5.12
        text-success on #e9ecef       2.64    4.32
        badge-success                 3.13    5.12
        alert-warning                 4.96    7.34
        alert-success                 6.99    7.56

THE BUTTON FAMILIES GET NOTHING, AND THAT IS THE POINT
    All 52 were read out before deciding. Every one is an ACTION: Save,
    Add, Create family, Update Meal Plan, Generate List, Add Unit, View,
    Email, WhatsApp, Continue, Try again, Show recipes, Apply Filters,
    Done - and on the amber side, Edit, Edit Recipe, Save & Recalculate,
    Missing Conversions. Not one is a status.

    base's own action standard settled this already, in the sentence
    "Colour is by WEIGHT, not by verb", under a measurement that reads
    "btn-info 60, btn-secondary 26, btn-success 13, btn-danger 9,
    btn-warning 6 - which is to say the colours meant nothing."

    So giving them a house green would be worse than leaving them alone.
    It would make 52 buttons look deliberate while still being drift,
    and it would hide them from Show-ButtonDrift and from a walkthrough
    that is about to go screen by screen looking for exactly this. And
    they are not an unserved case: every one sits in a position the house
    already has a component for -

        .page-action-buttons   ~18 of them, in bars already migrated
        a modal footer          9 of them, beside 27 .action-primary and
                                59 .action-secondary already in footers
        an inline form submit   5
        a card CTA / a cell     the rest

    They want the MARKUP, in a round that can weigh which control on a
    page is the primary one. view_recipe.html has five greens and four
    ambers in one bar; that is a hierarchy decision, not a colour.

    test_good_warn.py FAILS if a button family ever appears in base.

TWO PAGES GIVE UP A COPY
    property_detail.html   .badge-success - already var(--alv-good) and
                           var(--alv-on-accent), the exact rule this
                           round puts in base. The page reached the same
                           answer on its own; base is where it belongs.
                           Its .badge-info goes too: a hex and the
                           keyword `white`, both banned by 3.1, and base
                           has owned that rule since the accent round.
    tenant_add.html        .alert-success - Bootstrap's own three values
                           re-typed by hand.

ONE PAGE KEEPS ITS COPY, ON PURPOSE
    manual_pdf.html is a PRINT document and overrides five of these on
    purpose - flat, ink-cheap tones with a 3pt left rule and no border on
    the other three sides. Its style block sits after base's, so it wins,
    and it should. Measured: base's border-color lands on three sides
    that have no width there, so this round is invisible on that page.

Backups: .bak_goodwarn. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_goodwarn'
CRLF = {}

RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    """Write the backup and PROVE it is a copy (lesson 46)."""
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('H7: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70 - an anchor written with \\n matches nothing in a CRLF
    file, and property_detail.html is CRLF while base.html is not."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def drop_rule(css, sel):
    """Delete the rule whose selector list is exactly `sel`. Returns the
    new css, how many matched, and the declarations that were in it.

    The selector's start is computed from its own leading whitespace, not
    from m.start() - that sits after the PREVIOUS rule's closing brace,
    and cutting from there eats the rule before this one (H4).

    THE TAIL TRIM MUST CONSUME \\r. Every earlier round that carried this
    helper trimmed ' \\t' and then one '\\n', which is correct in an LF
    file and wrong in a CRLF one: the char after the closing brace is
    '\\r', the trim stops there, and the '\\r' is left behind as a blank
    line. property_detail.html is the first CRLF file a drop has been
    aimed at, and it showed up as two blank lines in the diff - not a
    defect on screen, but a file this round left untidy while claiming to
    tidy it."""
    want = ' '.join(sel.split())
    found = [m for m in RULE.finditer(css)
             if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                flags=re.S).split()) == want]
    if not found:
        return css, 0, None
    m = found[0]
    lead = len(m.group(1)) - len(m.group(1).lstrip())
    start = m.start() + lead
    head = css.rfind('\n', 0, start) + 1
    if css[head:start].strip():
        head = start
    tail = m.end()
    while tail < len(css) and css[tail] in ' \t\r':
        tail += 1
    if tail < len(css) and css[tail] == '\n':
        tail += 1
    return css[:head] + css[tail:], len(found), m.group(2)


# ==========================================================================
# THE FOUR TOKENS. Placed beside --alv-good and --alv-warn, in the
# semantic :root - not beside the rules, which live in the block that has
# to sit immediately after the Bootstrap link. That split is already
# proven in this file: .text-muted is declared in the first block and
# reads --alv-neutral out of the second one.
TOK_GOOD_AT = '        --alv-good-soft:  #e6f4ec;'
TOK_GOOD = """        --alv-good-ink:   #155737;   /* ink on the tint - measures 7.56  */
        --alv-good-line:  #bfe0cd;   /* the tint's own edge              */"""

TOK_WARN_AT = '        --alv-warn-soft:  #fdf3dd;'
TOK_WARN = """        --alv-warn-ink:   #6a4a05;   /* ink on the tint - measures 7.34  */
        --alv-warn-line:  #ecd39e;   /* the tint's own edge              */"""

# THE RULES. Appended after the INFO family's last line, in the block
# that sits after the Bootstrap link so these win without !important
# except where Bootstrap's own utility carries one.
RULES_AT = ('      a.text-info:hover, a.text-info:focus '
            '{ color: var(--alv-accent-ink) !important; }')
RULES = """

      /* ===== ALV SUCCESS AND WARNING v1 ===== 28 Sep 2026
         The last two Bootstrap families that carry a MEANING, answered
         the same way INFO is answered above. #28a745 measures 3.13 on
         white and 2.64 on the #e9ecef wash the panels are painted;
         #ffc107 measures 1.63 and 1.37. Six card heads make it worse by
         adding text-white - wcim_results heads a whole tier with white
         on #ffc107, which is 1.63 and unreadable.

         A COLOUR IS SET ON EVERY FILL, not only a background. Bootstrap
         gives .badge-warning DARK ink because its yellow demands it;
         repainting only the background would have left #212529 on
         #8e6207.

         THE BUTTON FAMILIES ARE ABSENT ON PURPOSE. btn-success 40,
         btn-warning 8, btn-outline-success 4, and read out, every one is
         an action - Save, Add, Create, Generate, Email, Continue, Edit.
         The page-header action bar's standard below already settles
         that: colour on an action is by WEIGHT, not by verb.
         (Its marker name is not written out here - test_action_standard
         counts that token and expects to find it once, at the standard
         itself. Prose naming a marker is the same family as prose shaped
         like a CSS declaration, which base already warns about two
         blocks down.) Painting them here would make
         52 buttons look deliberate while still being drift, and hide
         them from Show-ButtonDrift. They want .action-primary and
         .action-secondary, in a round that can weigh which control on a
         page is the main one. test_good_warn.py fails if a
         btn-*success or btn-*warning selector ever appears in base. */
      .bg-success { background-color: var(--alv-good) !important; }
      .text-success { color: var(--alv-good) !important; }
      .border-success { border-color: var(--alv-good) !important; }
      .badge-success { background-color: var(--alv-good); color: var(--alv-on-accent); }
      .alert-success {
        background-color: var(--alv-good-soft);
        border-color: var(--alv-good-line);
        color: var(--alv-good-ink);
      }
      .list-group-item-success { background-color: var(--alv-good-soft); color: var(--alv-good-ink); }
      a.text-success:hover, a.text-success:focus { color: var(--alv-good-ink) !important; }

      .bg-warning { background-color: var(--alv-warn) !important; }
      .text-warning { color: var(--alv-warn) !important; }
      .border-warning { border-color: var(--alv-warn) !important; }
      .badge-warning { background-color: var(--alv-warn); color: var(--alv-on-accent); }
      .alert-warning {
        background-color: var(--alv-warn-soft);
        border-color: var(--alv-warn-line);
        color: var(--alv-warn-ink);
      }
      .list-group-item-warning { background-color: var(--alv-warn-soft); color: var(--alv-warn-ink); }
      a.text-warning:hover, a.text-warning:focus { color: var(--alv-warn-ink) !important; }"""

# Every selector the block above must declare exactly once, and the four
# a page must never see again.
NEW_SELS = [
    '.bg-success', '.text-success', '.border-success', '.badge-success',
    '.alert-success', '.list-group-item-success',
    'a.text-success:hover, a.text-success:focus',
    '.bg-warning', '.text-warning', '.border-warning', '.badge-warning',
    '.alert-warning', '.list-group-item-warning',
    'a.text-warning:hover, a.text-warning:focus',
]
BANNED = ['btn-success', 'btn-warning', 'btn-outline-success',
          'btn-outline-warning']

# .icon-save's border literal IS --alv-good-line. Naming it here is the
# same move the tag inks got: the class reads the name instead of
# repeating the colour, and pointing it somewhere else later is one line.
SAVE_WAS = '      .icon-save   { color: var(--alv-good); border-color: #bfe0cd; }'
SAVE_NOW = ('      .icon-save   { color: var(--alv-good); '
            'border-color: var(--alv-good-line); }')

# THE STANDARDS BLOCK, UPDATED IN THE SAME ROUND - base's own first rule
# for changing base.
IDX_WAS = ('    Meaning    --alv-good  --alv-warn  --alv-bad  --alv-info  '
           '--alv-danger\n'
           '               (each with a -soft companion for backgrounds)')
IDX_NOW = ('    Meaning    --alv-good  --alv-warn  --alv-bad  --alv-info  '
           '--alv-danger\n'
           '               (each with a -soft companion for backgrounds;\n'
           '                good and warn also -ink and -line, as accent has)')

# base's own first rule for changing base is that the standards block is
# updated in the same round, and test_standards_doc.py enforces the count.
# Four tokens in means the sentence that names the total moves too.
COUNT_WAS = '  62 design tokens and the component classes below.'
COUNT_NOW = '  66 design tokens and the component classes below.'

DOC_AT = '      for weeks. NEVER: a semantic token used for decoration.'
DOC_NEW = """

      3.1a BOOTSTRAP'S OWN COLOUR FAMILIES           [test_good_warn.py]

      Bootstrap 4.1.3 is linked from a CDN and ships its own meanings.
      base answers the three that overlap ours, in the style block that
      must stay immediately after that link:

          info     -> --alv-accent     bg text border badge alert
                                       list-group-item, a:hover
          success  -> --alv-good       the same seven
          warning  -> --alv-warn       the same seven

      So `class="badge badge-success"` is house green with no page rule,
      and an alert a page builds inside a JS string is covered too,
      because the class is the same either way.

      THE BUTTON FAMILIES ARE DELIBERATELY NOT ANSWERED. btn-success,
      btn-warning and btn-outline-success are worn 52 times and not once
      as a status - they are Save, Add, Create, Generate, Email,
      Continue, Edit. Giving them a house tint would make drift look
      deliberate and hide it from Show-ButtonDrift.py. An action takes
      .action-primary or .action-secondary, by WEIGHT, per 3.1. A suite
      fails if a btn-* family ever appears in base."""

# ==========================================================================
# What two pages stop saying, now that base says it.
#   (file, selector, why)
PAGE_DROPS = [
    ('property_detail.html', '.badge-success',
     'the same rule, on the same two tokens - base is where it belongs'),
    ('property_detail.html', '.badge-info',
     'a hex and the keyword `white`; base has owned this since the accent '
     'round'),
    ('tenant_add.html', '.alert-success',
     "Bootstrap's own three values, re-typed"),
]

# ==========================================================================
print('=' * 74)
print('SECTION H, ROUND H7 - THE GREEN AND THE AMBER%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed = already = 0

# ------------------------------------------------------------- base first
bp = os.path.join(ROOT, 'base.html')
with open(bp, 'rb') as fh:
    braw = fh.read()
btext = read(bp)

if '--alv-good-ink' in btext:
    print('  %-34s already answers success and warning' % 'base')
    already += 1
else:
    for name, at, new in (('--alv-good-ink/-line', TOK_GOOD_AT, TOK_GOOD),
                          ('--alv-warn-ink/-line', TOK_WARN_AT, TOK_WARN)):
        a = eol(bp, at)
        if btext.count(a) != 1:
            raise SystemExit('H7: base - %r is there %d time(s), not 1'
                             % (at.strip(), btext.count(a)))
        btext = btext.replace(a, a + eol(bp, '\n' + new), 1)
        print('  %-34s + %s' % ('base', name))

    a = eol(bp, RULES_AT)
    if btext.count(a) != 1:
        raise SystemExit("H7: base - the INFO family's last line is there "
                         '%d time(s), not 1' % btext.count(a))
    btext = btext.replace(a, a + eol(bp, RULES), 1)
    print('  %-34s + 14 rules, mirroring the INFO family' % 'base')

    a, b = eol(bp, SAVE_WAS), eol(bp, SAVE_NOW)
    if btext.count(a) != 1:
        raise SystemExit('H7: base - .icon-save is there %d time(s), not 1'
                         % btext.count(a))
    btext = btext.replace(a, b, 1)
    print('  %-34s  .icon-save reads --alv-good-line, not #bfe0cd' % 'base')

    a, b = eol(bp, COUNT_WAS), eol(bp, COUNT_NOW)
    if btext.count(a) != 1:
        raise SystemExit('H7: base - the token-count sentence is there %d '
                         'time(s), not 1' % btext.count(a))
    btext = btext.replace(a, b, 1)

    a, b = eol(bp, IDX_WAS), eol(bp, IDX_NOW)
    if btext.count(a) != 1:
        raise SystemExit('H7: base - the Meaning index line is there %d '
                         'time(s), not 1' % btext.count(a))
    btext = btext.replace(a, b, 1)

    a = eol(bp, DOC_AT)
    if btext.count(a) != 1:
        raise SystemExit('H7: base - the 3.1 NEVER line is there %d time(s), '
                         'not 1' % btext.count(a))
    btext = btext.replace(a, a + eol(bp, DOC_NEW), 1)
    print('  %-34s  standards 3.1a written in the same round' % 'base')
    changed += 1

    # ---- the gates, before anything is written
    styles = [m.group(1) for m in
              re.finditer(r'<style\b[^>]*>(.*?)</style\s*>', btext,
                          re.S | re.I)]
    css = '\n'.join(styles)
    for sel in NEW_SELS:
        want = ' '.join(sel.split())
        n = sum(1 for m in RULE.finditer(css)
                if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                   flags=re.S).split()) == want)
        if n != 1:
            raise SystemExit('H7: base declares %r %d time(s), not 1'
                             % (sel, n))
    for m in RULE.finditer(css):
        names = re.sub(r'/\*.*?\*/', ' ', m.group(1), flags=re.S)
        for bad in BANNED:
            if re.search(r'\.' + re.escape(bad) + r'\b', names):
                raise SystemExit(
                    'H7: base has a rule for .%s. A green or amber BUTTON '
                    'is an action wearing a status colour; it takes '
                    '.action-primary or .action-secondary, not a house '
                    'tint. See 3.1a.' % bad)
    # every new declaration reads a token - no hex escaped into a rule
    blk = RULES
    for m in re.finditer(r'#[0-9a-fA-F]{3,8}\b', re.sub(r'/\*.*?\*/', ' ',
                                                        blk, flags=re.S)):
        raise SystemExit('H7: a hex literal (%s) is in the rules, not in the '
                         'token block' % m.group(0))

    if not CHECK:
        back_up(bp, braw)
        write(bp, btext)

# --------------------------------------------------------------- the pages
for rel, sel, why in PAGE_DROPS:
    path = os.path.join(ROOT, rel)
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)
    label = '%s %s' % (rel.replace('.html', ''), sel)

    blocks = [(m.start(1), m.end(1)) for m in
              re.finditer(r'<style\b[^>]*>(.*?)</style\s*>', text,
                          re.S | re.I)]
    hit = None
    for s, e in blocks:
        new, n, decls = drop_rule(text[s:e], sel)
        if n:
            hit = (s, e, new, n, decls)
            break

    if hit is None:
        print('  %-42s already gone' % label)
        already += 1
        continue
    s, e, new, n, decls = hit
    if n != 1:
        raise SystemExit('H7: %s declares %r %d times, not 1'
                         % (rel, sel, n))
    print('  %-42s - %s' % (label, why))
    text = text[:s] + new + text[e:]
    changed += 1
    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
print('  %d changed, %d already in place' % (changed, already))
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
