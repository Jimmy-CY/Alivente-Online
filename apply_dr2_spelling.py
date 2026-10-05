"""DR-2a - TWELVE DECLARATIONS THAT SAY WHAT BASE ALREADY SAYS.

   CS-1's section 5b has been printing, survey only, since 4 Oct:

       140 page declarations beat base's head stylesheets with a
       different value, on 30 pages.

   That number is frozen at CS-1 - the survey reads the tree as CS-1 left
   it, which is the right scope for a claim about CS-1 and the wrong one
   for a round. Re-measured live, after DR-1, PD-3, WS-1, FN-1 and OI-1:

       77 declarations on 16 pages

   AND SIX OF THOSE ARE NOT DRIFT AT ALL. manual_pdf.html does not
   extend base - it is rendered by render_to_string and handed to
   xhtml2pdf, so base's stylesheets never reach it and it has no choice
   but to style itself. Twelve templates in this tree are standalone like
   that. CS-2 teaches the census about them; this round leaves them
   alone. 71 on 15 pages.

   OF THOSE 71, TWELVE SAY THE SAME THING IN DIFFERENT WORDS:

   OF THOSE 71, SIXTEEN SAY THE SAME THING IN DIFFERENT WORDS:

       border-radius: 6px            vs  var(--alv-radius-sm)   (6px)
       background: #f8f9fa           vs  var(--alv-surface)
       background: white             vs  var(--alv-paper)
       color: white                  vs  #fff
       color: #0e7c8b                vs  var(--alv-view)
       grid-template-columns:
           1fr 1fr 1fr               vs  repeat(3, 1fr)
       transition: ... 0.15s ease    vs  ... .15s ease

   SIXTEEN, AND THE FIRST BUILD FOUND TWELVE. Its normaliser resolved
   var(), flattened repeat() and stripped a leading zero, and did not
   know that `white` is #ffffff. Four declarations spelling white two
   ways sat in the pile marked "really differs", where they would have
   been read as a page deliberately disagreeing with base about a
   colour. A colour normaliser that does not know the colour keywords is
   not a colour normaliser; this one now folds the keywords, expands
   three-digit hex and flattens rgb() spacing, and section 4 of the
   suite re-runs the whole classification on every push.

   Every one resolves to the byte-identical computed value. Deleting
   them cannot move a pixel, and section 3 renders what can be rendered
   at four widths to prove it rather than to assert it.

   WHAT IT BUYS IS NOT TIDINESS. A page that writes 6px is pinned to 6px
   for ever; a page that writes var(--alv-radius-sm) moves when the house
   moves. Five pages rejoin the token system at a cost of nothing.

   THE OTHER 55 ARE NOT THIS ROUND. Forty are a colour literal that does
   NOT match base's token, thirteen are a real size difference, and six
   are layout - of which four look deliberate, because title_deeds has
   two actions in its bar and physical_invoice_list has six. Each of
   those changes a pixel and needs a decision and a render. Lumping them
   in here would turn a round that cannot go wrong into one that can.

   FILES: five templates.                        [test_dr2_spelling.py]
"""
import os
import sys

import alv_tree as T
import alv_cssrules as R

SUFFIX = '.bak_dr2spell'

M768 = '@media screen and (max-width: 768px) && '

# (page, selector as rule_spans reports it, property, the value it writes)
DROP = [
    ('customer_invoice_form.html', '.icon-action-btn', 'border-radius', '6px'),
    ('customer_invoice_form.html', '.icon-action-btn', 'background', 'white'),
    ('customer_invoice_form.html', '.icon-delete:hover', 'color', 'white'),
    ('physical_invoice_edit.html', '.icon-action-btn', 'border-radius', '6px'),
    ('physical_invoice_edit.html', '.icon-action-btn', 'background', 'white'),
    ('physical_invoice_edit.html', '.icon-delete:hover', 'color', 'white'),

    ('passport_management.html', M768 + '.mobile-action-bar',
     'grid-template-columns', '1fr 1fr 1fr'),
    ('passport_management.html', M768 + '.mobile-action-btn',
     'border-radius', '6px'),
    ('passport_management.html', M768 + '.mobile-action-btn',
     'transition', 'background-color 0.15s ease'),

    ('physical_invoice_list.html', M768 + '.mobile-action-btn',
     'background', '#f8f9fa'),
    ('physical_invoice_list.html', M768 + '.mobile-action-btn',
     'border-radius', '6px'),
    ('physical_invoice_list.html', M768 + '.mobile-action-btn',
     'transition', 'background-color 0.15s ease'),

    ('title_deeds_management.html', M768 + '.icon-color-view',
     'color', '#0e7c8b'),
    ('title_deeds_management.html', M768 + '.mobile-action-btn',
     'background', '#f8f9fa'),
    ('title_deeds_management.html', M768 + '.mobile-action-btn',
     'border-radius', '6px'),
    ('title_deeds_management.html', M768 + '.mobile-action-btn',
     'transition', 'background-color 0.15s ease'),
]

NOTE = ('    /* DR-2a, 5 Oct 2026 - %d declaration(s) removed from this\n'
        '       page because base already said them, in its own words.\n'
        '       Each resolved to the byte-identical computed value, so\n'
        '       nothing here moved; what changes is that the page is on\n'
        '       the token again and will follow when the house does.\n'
        '       The ones that really DO differ from base are a separate\n'
        '       round, because those move a pixel.          [CS-1 5b] */\n')


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
    if '\r\n' in text:
        return block.replace('\r\n', '\n').replace('\n', '\r\n')
    return block.replace('\r\n', '\n')


def find_rule(text, selector):
    """Every rule in the page whose selector is exactly this one."""
    out = []
    for a, b in R.style_spans(text):
        for sel, ba, bb, ra, rb in R.rule_spans(text, a, b):
            if sel == selector:
                out.append((ba, bb))
    return out


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    bypage = {}
    for page, sel, prop, want in DROP:
        bypage.setdefault(page, []).append((sel, prop, want))

    dropped = 0
    touched = 0
    for page, items in sorted(bypage.items()):
        path = T.path_of(page)
        if not path:
            raise SystemExit('DR-2a: %s is not in this checkout' % page)
        text = read(path)
        if 'DR-2a, 5 Oct 2026' in text:
            continue

        # HIGHEST OFFSET FIRST, so removing one declaration cannot move
        # the span of the next. The first build of a round like this
        # deleted forwards and corrupted the second rule it touched.
        cuts = []
        for sel, prop, want in items:
            rules = find_rule(text, sel)
            if len(rules) != 1:
                raise SystemExit('DR-2a: %s on %s matched %d rule(s), '
                                 'expected 1' % (sel, page, len(rules)))
            ba, bb = rules[0]
            span = R.decl_span(text, ba, bb, prop)
            if not span:
                raise SystemExit('DR-2a: %s has no %s in %s on %s'
                                 % (sel, prop, sel, page))
            s, e = span
            frag = ' '.join(text[s:e].split())
            if want.lower() not in frag.lower():
                raise SystemExit('DR-2a: %s { %s } on %s reads %r, not %r - '
                                 'it has changed since this was measured'
                                 % (sel, prop, page, frag, want))
            cuts.append((s, e))

        for s, e in sorted(cuts, reverse=True):
            text = text[:s] + text[e:]
        dropped += len(cuts)
        touched += 1

        # The note goes at the top of the LAST style block, which is the
        # page's own - the same block CS-1 moved out of base.
        spans = R.style_spans(text)
        at = spans[-1][0]
        text = text[:at] + fit(text, NOTE % len(cuts)) + text[at:]

        if not check:
            backup(path)
            write(path, text)

    print('DR-2a  declarations dropped : %d' % dropped)
    print('DR-2a  pages                : %d' % touched)
    if check:
        if dropped:
            print('DR-2a  NOT APPLIED')
            return 1
        print('DR-2a  applied')
        return 0
    if dropped not in (0, len(DROP)):
        print('DR-2a  REFUSED: partial application (%d of %d)'
              % (dropped, len(DROP)))
        return 2
    print('DR-2a  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
