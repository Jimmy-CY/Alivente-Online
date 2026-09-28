# -*- coding: utf-8 -*-
"""SECTION G, ROUND G3b-2 - THE RECIPES HUB GIVES UP ITS OWN ACTION BAR

The sixth and last Personal page with no house action bar, and the one
that most looked like it had one. recipe_management.html does not
hand-roll a header the way G3b-1's five did - it hand-rolls THE WHOLE
COMPONENT:

    .top-button-bar        is .page-action-buttons
    .top-button-group      and .top-button-right are its two halves
    .action-more-wrapper   .action-more-btn, .action-more-menu,
    .action-more-item      .action-more-divider - all of base's names,
                           declared again locally

Sixteen of its bar rules are base's, re-typed. The markup already wears
.action-primary, .action-secondary and .action-back - but the paint
underneath comes from Bootstrap, so the bar reads as green and blue
buttons that happen to be labelled with house names.

THE ONE THING THAT WAS ACTUALLY HARD, AND WHY IT IS NOT
    Add Recipe and Settings are SPLIT BUTTONS - a label with a chevron
    that opens a menu. The first cut of this round moved the bar over and
    left .action-primary where it was, on the CONTAINER:

        <div class="dropdown-btn-container action-primary">
          <button class="btn btn-success dropdown-btn"> Add Recipe
          <div class="dropdown-menu-custom"> ...

    and the phone came out reading "d Recip". base styles .action-primary
    as `display: inline-flex`, so the container became a flex ROW - and
    on a phone this page deliberately makes the menu `position: static`
    so it pushes content down. The 200px menu became a flex SIBLING of
    the button and took its share. Fixing the direction exposed a second
    collision on the cross axis, and that exposed a third in the
    collapsed menu's box. Three fixes deep, each uncovering the next.

    The cause was none of those. IT WAS A HOUSE CLASS ON A WRAPPER THAT
    IS NOT A BUTTON. base's button rules are written for buttons; hang
    one on a positioning div and base starts laying out its children.
    So the tone moves ONE ELEMENT IN, onto the control it describes:

        <div class="dropdown-btn-container">
          <button class="btn action-primary dropdown-btn"> Add Recipe

    and all three collisions are gone at once, because base is no longer
    looking at the container at all. Measured at both widths: nothing
    clipped, nothing overflowing.

    A split button therefore keeps working on a phone exactly as it does
    now, which is what it did before this round too.

WHAT CHANGES
    1. The title: <h2><center>RECIPE MANAGEMENT</center></h2> becomes
       .page-title-h2, and the line under it .page-subtitle-h4 - the same
       shape passport_management carries.
    2. .top-button-bar becomes .page-action-buttons and its two inner
       wrapper divs go, so the controls are direct children as they are
       on every other bar in the system.
    3. The tone classes move onto the buttons, and the Bootstrap ones -
       btn-success, btn-primary, btn-secondary - come off.
    4. Sixteen local rules go. .action-more-divider goes UP into base,
       where the rest of that menu already lives and which declared no
       such name - which is why the one page that wanted a divider kept
       the whole menu locally to get it.

A TAP TARGET, FOR FREE
    The local rules size these controls at 38px on a phone. base sizes
    them at 44, which is its tap-target standard. Deleting the copies
    raises them without this round mentioning height once.

WHAT IS KEPT
    THE SPLIT BUTTON ITSELF - .dropdown-btn-container, .dropdown-btn,
    .dropdown-menu-custom and the tap-to-toggle script behind them.
    base has .action-more-btn, which is an ICON opening a menu, and no
    component for a labelled one. finance_pl_act has the only other one
    in the tree and hand-rolls it too. A component with two hand-rolled
    instances is worth writing down; it is not worth inventing in the
    middle of this round.

    THE FAVOURITES TOGGLE. Its colour is written in the template -
    btn-danger when the filter is on, btn-outline-danger when it is off -
    so the colour IS the state. Show-ButtonDrift.py already records that
    category as "colour is template logic (a segmented toggle)" and
    leaves it alone. So does this round.

NOT DONE HERE, AND WORTH MORE THAN THIS ROUND
    base owns the More menu's markup and its CSS but NOT its behaviour,
    so the ~30 lines that open it are written out in TWENTY-NINE pages,
    this one among them. Counted, not estimated. Its own round.

Backups: .bak_hubbar. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_hubbar'
REL = 'recipe_management.html'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
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
            raise SystemExit('G3b-2: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def styles_of(t):
    return [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]


def blanked(t):
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


# ==========================================================================
# WHAT base GAINS, beside the rest of the menu it belongs to.
B_ANCHOR = '        .action-more-item-danger {'
B_NEW = """        /* The rule between two groups of menu items. Only
           recipe_management has ever drawn one, in its own copy of this
           menu, and base declared no such name - so the one page that
           wanted a divider kept the whole component locally to get it.
           Already on a token when it arrived; it only had to move. */
        .action-more-divider {
          height: 1px;
          background: var(--alv-surface-deep);
          margin: 6px 0;
        }

"""

HEAD_WAS = ('<h2><center>RECIPE MANAGEMENT</center></h2>\n'
            '<h4><center>CREATE / VIEW / EDIT / DELETE RECIPES</center></h4>')
HEAD_NOW = ('<h2 class="page-title-h2">RECIPE MANAGEMENT</h2>\n'
            '<h4 class="page-subtitle-h4">CREATE / VIEW / EDIT / DELETE '
            'RECIPES</h4>')

BAR_WAS = '<div class="top-button-bar">'
BAR_NOW = '<div class="page-action-buttons">'
INNER = ['<div class="top-button-group">', '<div class="top-button-right">']

# THE TONE MOVES ONE ELEMENT IN. A house class on a wrapper makes base
# lay out that wrapper's children; on the control it describes, it paints.
#   (exact class attribute, what replaces it, how many)
TONE = [
    # the two split-button wrappers give their tone to their buttons
    ('dropdown-btn-container action-primary', 'dropdown-btn-container', 1),
    ('dropdown-btn-container action-secondary', 'dropdown-btn-container', 1),
    ('btn btn-success dropdown-btn', 'btn action-primary dropdown-btn', 1),
    ('btn btn-secondary dropdown-btn action-primary',
     'btn action-primary dropdown-btn', 1),
    ('btn btn-secondary dropdown-btn', 'btn action-secondary dropdown-btn',
     1),
    # and the plain ones drop Bootstrap
    ('btn btn-primary action-secondary', 'btn action-secondary', 2),
    ('btn btn-success action-secondary', 'btn action-secondary', 1),
    ('btn btn-success action-more-btn', 'btn action-more-btn', 1),
]

# base declares every one of these. ('sel', 2) where the page writes it
# once for the desktop and again in its own phone block.
KILL = [
    ('.top-button-bar', 2),
    ('.top-button-group', 2),
    ('.top-button-right', 2),
    ('.top-button-right .action-more-wrapper', 2),
    '.top-button-group .action-secondary',
    '.top-button-group .action-primary',
    '.top-button-right .action-secondary',
    '.top-button-right .action-more-btn',
    '.action-more-menu',
    '.action-more-item',
    '.action-more-item i',
    '.action-more-item:hover, .action-more-item:active, '
    '.action-more-item:focus',
    '.top-button-right .action-back',
    '.action-more-divider',          # goes UP into base, not away
]

# Keyed on a wrapper that stops existing. The rule is page logic - it
# sizes the split button on a phone - so it is repointed, not deleted.
# The 38px goes with it: base makes a phone control 44px and this was the
# only thing holding it at 38.
REPOINT = [('.top-button-group .action-primary .dropdown-btn',
            '.page-action-buttons .dropdown-btn-container .dropdown-btn',
            'height: 38px;')]

KEEP = ['.dropdown-btn-container', '.dropdown-btn', '.dropdown-menu-custom',
        '.dropdown-menu-custom a']

# WHAT base CANNOT DO FOR A SPLIT BUTTON, because it has no component for
# one. Three rules, each answering something measured at 390px.
PAGE_CSS = """
            /* A SPLIT BUTTON IS A CONTROL INSIDE A WRAPPER, and base's
               phone rules are written for the control. Three things
               follow, all measured:

               1. base hides .action-secondary when the bar has a More
                  button - but that hides the BUTTON, not the div round
                  it, so Settings left a 200px empty wrapper and pushed
                  Back 152px off the end of the bar.
               2. the primary wrapper is not a flex item base knows
                  about, so it sized to content (200px) where every
                  other house primary fills the row.
               3. the collapsed menu still has a border and a margin, so
                  its wrapper stood 54px tall beside 44px siblings.

               base uses :has() itself, so this invents no technique. */
            .page-action-buttons
                .dropdown-btn-container:has(.action-secondary) {
              display: none;
            }
            .page-action-buttons
                .dropdown-btn-container:has(.action-primary) {
              flex: 1 1 auto;
              min-width: 0;
            }
            .page-action-buttons .dropdown-btn-container
                .dropdown-menu-custom {
              margin-top: 0;
              border-width: 0;
            }
            .page-action-buttons .dropdown-btn-container.mobile-active
                .dropdown-menu-custom {
              margin-top: 6px;
              border-width: 2px;
            }
"""


def div_end(scan, start):
    d = 0
    for m in re.finditer(r'</?div\b', scan[start:]):
        d += 1 if m.group(0) == '<div' else -1
        if d == 0:
            return start + m.end() + scan[start + m.end():].index('>') + 1
    raise SystemExit('G3b-2: unbalanced <div> from %d' % start)


def drop_rule(css, sel):
    want = ' '.join(sel.split())
    found = [m for m in RULE.finditer(css)
             if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                flags=re.S).split()) == want]
    if not found:
        return None, 0, None
    m = found[0]
    lead = len(m.group(1)) - len(m.group(1).lstrip())
    start = m.start() + lead
    head = css.rfind('\n', 0, start) + 1
    if css[head:start].strip():
        head = start
    tail = m.end()
    while tail < len(css) and css[tail] in ' \t':
        tail += 1
    if tail < len(css) and css[tail] == '\n':
        tail += 1
    return css[:head] + css[tail:], len(found), m.group(2)


# ==========================================================================
print('=' * 74)
print('SECTION G, ROUND G3b-2 - THE RECIPES HUB%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed = already = 0

# ------------------------------------------------------------- base first
bp = os.path.join(ROOT, 'base.html')
btext = read(bp)
if '.action-more-divider' in btext:
    print('  %-34s already declares .action-more-divider' % 'base')
    already += 1
else:
    a = eol(bp, B_ANCHOR)
    if btext.count(a) != 1:
        raise SystemExit('G3b-2: base - .action-more-item-danger is at that '
                         'indent %d time(s), not 1' % btext.count(a))
    btext = btext.replace(a, eol(bp, B_NEW) + a, 1)
    print('  %-34s + .action-more-divider (moved up, already on a token)'
          % 'base')
    changed += 1
    if not CHECK:
        with open(bp, 'rb') as fh:
            back_up(bp, fh.read())
        write(bp, btext)

# -------------------------------------------------------------- the page
path = os.path.join(ROOT, REL)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)

if 'page-action-buttons' in text:
    print('  %-34s already on the house bar' % REL.replace('.html', ''))
    already += 1
else:
    h = eol(path, HEAD_WAS)
    if text.count(h) != 1:
        raise SystemExit('G3b-2: the <h2><center> heading pair is there %d '
                         'time(s), not 1' % text.count(h))
    text = text.replace(h, eol(path, HEAD_NOW), 1)

    if text.count(BAR_WAS) != 1:
        raise SystemExit('G3b-2: .top-button-bar appears %d time(s), not 1'
                         % text.count(BAR_WAS))
    text = text.replace(BAR_WAS, BAR_NOW, 1)

    for opener in INNER:
        scan = blanked(text)
        i = scan.find(opener)
        if i < 0:
            raise SystemExit('G3b-2: %s is not there' % opener)
        j = div_end(scan, i)
        inner = text[i + len(opener):j - len('</div>')]
        text = text[:i] + inner.strip('\r\n') + text[j:]

    toned = 0
    for was, now_cls, n in TONE:
        seen = text.count('class="%s"' % was)
        if seen != n:
            raise SystemExit(
                'G3b-2: class="%s" appears %d time(s), and this round was '
                'written against %d.' % (was, seen, n))
        text = text.replace('class="%s"' % was, 'class="%s"' % now_cls)
        toned += n

    bar = blanked(text)
    bi = bar.find(BAR_NOW)
    be = div_end(bar, bi)
    left = re.findall(r'\bbtn-(?:success|primary|secondary)\b', bar[bi:be])
    if left:
        raise SystemExit('G3b-2: %d Bootstrap tone(s) left in the bar: %s'
                         % (len(left), left[:4]))

    # NO HOUSE CLASS ON A WRAPPER. This is the whole lesson of the round,
    # so it is a gate, not a comment: base's button rules lay out their
    # own children, and a positioning div that wears one stops being a
    # positioning div.
    for m in re.finditer(r'<div[^>]*class="([^"]*)"', bar[bi:be]):
        names = m.group(1).split()
        if 'dropdown-btn-container' in names and (
                'action-primary' in names or 'action-secondary' in names):
            raise SystemExit(
                'G3b-2: a .dropdown-btn-container still wears a tone class. '
                'base styles .action-primary as inline-flex, which turns a '
                'split button\'s menu into a flex sibling of its own '
                'button - measured at 390px, "Add Recipe" came out 44px '
                'wide and read "d Recip".')

    gone = 0
    moved_body = None
    for entry in KILL:
        sel, want = entry if isinstance(entry, tuple) else (entry, 1)
        seen = sum(drop_rule(text[a2:b2], sel)[1]
                   for (a2, b2) in styles_of(text))
        if seen != want:
            raise SystemExit('G3b-2: "%s" is worn by %d rule(s); this round '
                             'was written against %d.' % (sel, seen, want))
        for _ in range(want):
            for (a2, b2) in styles_of(text):
                new_css, k, body = drop_rule(text[a2:b2], sel)
                if k:
                    if sel == '.action-more-divider':
                        moved_body = ' '.join(body.split())
                    text = text[:a2] + new_css + text[b2:]
                    gone += 1
                    break
    if moved_body is None or 'var(--alv-surface-deep)' not in moved_body:
        raise SystemExit('G3b-2: the divider rule that went up to base was '
                         'not the one this round read: %s' % moved_body)

    for was, now_sel, drop in REPOINT:
        n = 0
        for (a2, b2) in styles_of(text):
            css = text[a2:b2]
            for m in RULE.finditer(css):
                if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                   flags=re.S).split()) != was:
                    continue
                body = m.group(2)
                if drop and drop not in ' '.join(body.split()):
                    raise SystemExit('G3b-2: %s does not carry %r'
                                     % (was, drop))
                body = re.sub(re.escape(drop) + r'\s*', '', body)
                text = (text[:a2] + css[:m.start(1)] + '\n' + now_sel + ' '
                        + css[m.start(1) + len(m.group(1)):m.start(2)]
                        + body + css[m.end(2):] + text[b2:])
                n += 1
                break
            if n:
                break
        if n != 1:
            raise SystemExit('G3b-2: "%s" was repointed %d time(s), not 1'
                             % (was, n))

    # the three rules base cannot supply - see PAGE_CSS above
    hook = '.page-action-buttons .dropdown-btn-container .dropdown-btn'
    n = 0
    for (a2, b2) in styles_of(text):
        css = text[a2:b2]
        for m in RULE.finditer(css):
            if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                               flags=re.S).split()) != hook:
                continue
            text = (text[:a2] + css[:m.end()] + eol(path, PAGE_CSS)
                    + css[m.end():] + text[b2:])
            n += 1
            break
        if n:
            break
    if n != 1:
        raise SystemExit('G3b-2: the phone rules were added %d time(s), '
                         'not 1' % n)

    for sel in KEEP:
        here = any(' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                   flags=re.S).split()) == sel
                   for (a2, b2) in styles_of(text)
                   for m in RULE.finditer(text[a2:b2]))
        if not here:
            raise SystemExit('G3b-2: "%s" is page logic this round promised '
                             'to keep, and it is gone.' % sel)

    print('  %-34s title, bar, %d tone(s), %d rule(s), 1 repoint'
          % (REL.replace('.html', ''), toned, gone))
    changed += 1
    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
print('  %d file(s) changed, %d already done.' % (changed, already))
print('=' * 74)
