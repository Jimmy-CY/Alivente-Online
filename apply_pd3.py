"""PD-3 - PROPERTY DETAIL STOPS CARRYING ITS OWN PALETTE, AND STOPS
   SCROLLING SIDEWAYS ON EVERY PHONE.

   property_detail.html is the biggest page in the app: 102 KB, 1,825
   lines, one <style> block. PD-1 took its seven dark table headers and
   PD-2 brought the tables onto base's component. What was left is what
   this round takes.

   FOUR PARTS. Demetri, 5 Oct 2026, asked for them in one round.

   -------------------------------------------------------------------
   A. THE SEVEN PIXELS

   Measured, before anything was changed:

       320px  scrollWidth 327   over +7    container pad 8px
       390px  scrollWidth 397   over +7    container pad 8px
       768px  scrollWidth 775   over +7    container pad 8px
       992px  scrollWidth 992   over +0    container pad 15px

   Every phone and every tablet scrolls sideways; desktop does not. The
   cause is one rule in the page's own mobile block:

       @media screen and (max-width: 768px) {
           .property-detail-page.container-fluid {
               padding-left: 8px; padding-right: 8px;
           }
       }

   Bootstrap's .row pulls `margin: 0 -15px`, and the wrapper only gives
   back 8. 15 - 8 = 7, each side. The columns then add their own 15px of
   padding back, so the CONTENT lines up and only the row boxes stick
   out - which is why this has been invisible to the eye and visible to
   the scrollbar.

   Demetri chose "keep the tighter gutters, pull the rows in". So the
   rows are given -8px to match the wrapper, and the columns inside them
   8px instead of 15px. The page keeps the tighter phone layout it was
   given on purpose, and the sideways scroll ends.

   SCOPED TO `> .row` AND `> .row > [class*="col"]`, deliberately. A bare
   `.row` rule would also catch rows nested inside cards and tables,
   which are not the ones overflowing and are not this round's to move.

   -------------------------------------------------------------------
   B. THE ONE CONTROL UNDER 44PX

   One, not three - I had three in my notes and the render says one:

       select.form-control.form-control-sm      103.0 x 41.0

   Bootstrap's .form-control-sm is 31px plus borders. The house floor is
   44 (C2, 'ALV TAP TARGET v1'). It gets min-height, not height, so a
   longer option cannot clip.

   -------------------------------------------------------------------
   C. EIGHTY-FOUR HEX LITERALS

   98 hex uses, 33 distinct values, and only 14 of those uses matched a
   token base already declares. The rest were Bootstrap's defaults and a
   handful of one-offs, every one of which base has a name for.

   THIS CHANGES COLOURS, AND THAT IS THE POINT. #28a745 is Bootstrap's
   green; --alv-good is #1e7d4f, which is deeper. The house rule is that
   a page does not keep its own palette: the token carries the meaning,
   and when the meaning is restyled every page follows. Demetri chose
   "all 84, onto base's tokens" with before and after renders.

   ONE VALUE IS MAPPED BY ITS ROLE, NOT ITS NUMBER. #6c757d is a muted
   ink in eleven places and an accent stripe in one. The first is
   --alv-ink-soft, the second --alv-neutral. Everything else means one
   thing wherever it appears.

   -------------------------------------------------------------------
   D. FIFTEEN RULES THAT COULD NEVER HAVE DONE ANYTHING

   Not all 39 !important declarations - only the ones that can be proved
   dead on paper rather than on a picture.

       .issues-table th.text-left { text-align: left !important; }

   Bootstrap 4.1.3 already ships:

       .text-left { text-align: left !important }

   and all 22 <th> on this page already carry the utility class. Same
   property, same value, same flag - the page's rule cannot change
   anything, on any row, rendered or not. Fifteen such rules go, taking
   14 of the 39 flags with them.

   THE OTHER 25 FLAGS STAY. I dropped each one and repainted, and 19
   changed nothing - but the fixture flattens the page's {% for %} loops
   and draws a fraction of the real rows. That measurement can prove a
   flag MATTERS; it cannot prove one does not. The survivors live in the
   mobile card layout, which is exactly where a three-row fixture is
   least trustworthy. They are left, and this comment is the record of
   why rather than a claim that they were checked.

   FILES: property_detail.html.                      [test_pd3.py]
"""
import os
import re
import sys

import alv_tree as T

SUFFIX = '.bak_pd3'
PAGE = 'property_detail.html'


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def once(text, needle, what):
    n = text.count(needle)
    if n != 1:
        raise SystemExit('PD-3: %s appears %d times, expected 1' % (what, n))
    return True


# ===================================================================== C

# value -> token. The colour each one MEANS, in base's words.
MAP = {
    # ink
    '#6c757d': '--alv-ink-soft',      # Bootstrap's muted grey
    '#2c3e50': '--alv-ink',           # the page's dark slate headings
    '#495057': '--alv-ink-strong',
    '#343a40': '--alv-ink',
    # surfaces
    '#f8f9fa': '--alv-surface',
    '#f9f9f9': '--alv-surface',
    '#ecf0f1': '--alv-surface-deep',
    # lines
    '#dee2e6': '--alv-line',
    '#ced4da': '--alv-line',
    '#eee': '--alv-line-soft',
    # accent
    '#0e7c8b': '--alv-accent',
    '#0c5460': '--alv-accent-ink',
    '#d1ecf1': '--alv-accent-soft',
    '#d1edff': '--alv-accent-soft',
    '#bee5eb': '--alv-accent-line',
    # good
    '#28a745': '--alv-good',
    '#27ae60': '--alv-good',
    '#218838': '--alv-good-ink',      # it was #28a745's hover
    '#155724': '--alv-good-ink',
    '#d4edda': '--alv-good-soft',
    '#f3fff3': '--alv-good-soft',
    # warn
    '#ffc107': '--alv-warn',
    '#856404': '--alv-warn-ink',
    '#fff3cd': '--alv-warn-soft',
    '#fff8dc': '--alv-warn-soft',
    '#ffeaa7': '--alv-warn-line',
    # bad
    '#dc3545': '--alv-bad',
    '#b00020': '--alv-bad',
    '#721c24': '--alv-bad-ink',
    '#f8d7da': '--alv-bad-soft',
    '#fff3f3': '--alv-bad-soft',
    '#fff5f5': '--alv-bad-soft',
    '#f1b0b7': '--alv-bad-line',
}

# THE ONE THAT DEPENDS ON ITS ROLE. #6c757d is a muted ink eleven times
# and the left stripe of a neutral card once. Same number, two meanings,
# and the whole point of a token is that the NAME carries the meaning.
BY_ROLE = {
    ('#6c757d', 'border-left'): '--alv-neutral',
}

HEX = re.compile(r'#[0-9a-fA-F]{3,8}\b')
DECL = re.compile(r'(^|[;{])\s*([-\w]+)\s*:\s*([^;{}]*)', re.M)


def paint_css(css):
    """Every hex inside a declaration becomes var(--token). Returns the
    new CSS and how many were replaced."""
    out = []
    last = 0
    done = 0
    for m in DECL.finditer(css):
        prop, val = m.group(2).lower(), m.group(3)
        if not HEX.search(val):
            continue
        new = val
        for h in set(HEX.findall(val)):
            key = h.lower()
            tok = BY_ROLE.get((key, prop)) or MAP.get(key)
            if not tok:
                continue
            new = re.sub(re.escape(h) + r'\b', 'var(%s)' % tok, new)
            done += val.lower().count(key)
        if new == val:
            continue
        a = m.start(3)
        out.append(css[last:a])
        out.append(new)
        last = m.end(3)
    out.append(css[last:])
    return ''.join(out), done


# INLINE style= ATTRIBUTES, which are not in the <style> block at all and
# were missed by the first census for exactly that reason.
INLINE = [
    ('style="cursor: pointer; color: #28a745; font-size: 1.2em;"',
     'style="cursor: pointer; color: var(--alv-good); font-size: 1.2em;"'),
    ('<span style="color:#b00020;">',
     '<span style="color:var(--alv-bad);">'),
]


# ===================================================================== A

GUTTER_OLD = '''    /* Page wrapper — tighter padding */
    .property-detail-page.container-fluid {
        padding-left: 8px;
        padding-right: 8px;
    }'''

GUTTER_NEW = '''    /* Page wrapper — tighter padding.
       PD-3, 5 Oct 2026: and the rows pulled in to match it.

       Bootstrap's .row carries `margin: 0 -15px`. This wrapper gives
       back only 8, so every row stuck out 7px each side and the page
       scrolled sideways at every width from 320 to 768. Measured:
       scrollWidth 397 against a 390 document.

       Demetri chose to keep the tighter gutters, so the rows come in to
       meet them rather than the wrapper going back out to 15.

       DIRECT CHILDREN ONLY. A bare `.row` would also catch the rows
       nested inside cards and tables, which never overflowed and are
       not this round's to move. */
    .property-detail-page.container-fluid {
        padding-left: 8px;
        padding-right: 8px;
    }
    .property-detail-page.container-fluid > .row {
        margin-left: -8px;
        margin-right: -8px;
    }
    .property-detail-page.container-fluid > .row > [class*="col-"] {
        padding-left: 8px;
        padding-right: 8px;
    }'''


# ===================================================================== B

TAP_ANCHOR = '''    .property-detail-page.container-fluid > .row > [class*="col-"] {
        padding-left: 8px;
        padding-right: 8px;
    }'''

TAP_NEW = TAP_ANCHOR + '''

    /* 44PX TO TAP - PD-3, 5 Oct 2026, and C2's floor.
       The page's one short select measured 103.0 x 41.0 at 390px.
       Bootstrap's .form-control-sm is 31px plus borders; the house floor
       is 44. min-height rather than height, so a long option cannot
       clip. */
    .property-detail-page select.form-control-sm,
    .property-detail-page .form-control-sm {
        min-height: 44px;
    }'''


# ===================================================================== D

DEAD = re.compile(
    r'[ \t]*\.[\w-]+-table\s+th\.text-(?:left|center|right)\s*\{[^{}]*\}'
    r'[ \t]*\r?\n?')


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    path = T.path_of(PAGE)
    text = read(path)
    gut = tap = dead = hexes = 0

    # --- A, the gutters
    if 'container-fluid > .row {' not in text:
        old = fit(text, GUTTER_OLD)
        once(text, old, 'the wrapper padding rule')
        text = text.replace(old, fit(text, GUTTER_NEW), 1)
        gut = 1

    # --- B, the tap target
    if '44PX TO TAP' not in text:
        old = fit(text, TAP_ANCHOR)
        once(text, old, 'the column padding rule')
        text = text.replace(old, fit(text, TAP_NEW), 1)
        tap = 1

    # --- D, the fifteen rules Bootstrap already says
    css_spans = [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I)]
    if css_spans:
        a, b = css_spans[0]
        css = text[a:b]
        css2, dead = DEAD.subn('', css)
        text = text[:a] + css2 + text[b:]

    # --- C, the palette
    css_spans = [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I)]
    if css_spans:
        a, b = css_spans[0]
        css2, hexes = paint_css(text[a:b])
        text = text[:a] + css2 + text[b:]
    for old, new in INLINE:
        o = fit(text, old)
        if o in text:
            once(text, o, 'an inline colour')
            text = text.replace(o, fit(text, new), 1)
            hexes += 1

    changed = gut or tap or dead or hexes
    if changed and not check:
        backup(path)
        write(path, text)

    print('PD-3  gutters           : %d' % gut)
    print('PD-3  tap target        : %d' % tap)
    print('PD-3  dead rules removed: %d' % dead)
    print('PD-3  colours tokenised : %d' % hexes)

    if check:
        if changed:
            print('PD-3  NOT APPLIED')
            return 1
        print('PD-3  applied')
        return 0
    if gut not in (0, 1) or tap not in (0, 1):
        print('PD-3  REFUSED: partial application')
        return 2
    print('PD-3  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
