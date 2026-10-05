"""WS-1 - THE LEFT STRIPE THAT MEANS WARNING, SAID ELEVEN WAYS BY HAND.

   PD-3 put property_detail's amber stripe onto var(--alv-warn) and its
   suite printed, on every run, how many were still spelt out elsewhere.
   This takes them.

   THE CENSUS WAS SHORT THE FIRST TIME, and that is the part worth
   writing down. Asked for `border-left: ... #ffc107` it returned eight
   declarations on seven pages. Three more pages paint the same stripe
   with the LONGHAND:

       home.html                      border-left-color: #ffc107;
       manual_pdf.html                border-left-color: #ffc107;
       projects/projects_delete.html  border-left-color: #ffc107;

   which is exactly the hole DR-1 fell into - a shorthand census that
   could not see the property form, so DR-1b had to exist a day later to
   collect fifteen rules the first pass had walked straight past. The
   pattern was widened BEFORE this patcher was written rather than after.

       8 x border-left: 4px solid #ffc107
       3 x border-left-color: #ffc107
      --
      11 declarations on 10 pages

   Four stripes already carry var(--alv-warn) - crs/submission_detail,
   finance_valuations_edit, tenant_payment_days and property_detail - so
   afterwards all fifteen in the app agree.

   WHAT THIS ROUND DOES NOT CLAIM. That #ffc107 leaves the tree. It does
   not: the colour appears 71 times on 26 pages - 17 backgrounds, 16 full
   borders, 14 outside a stylesheet altogether, and a scatter of
   border-color, border-bottom, color and border-top. Those are other
   families with other meanings and they are not this round's. The claim
   here is narrow and checkable: every LEFT STRIPE is on the token.

   THE COLOUR CHANGES, AND DEMETRI HAS SEEN IT. var(--alv-warn) is
   #8e6207, which reads olive rather than amber - yellow does that when
   you darken it to the weight of the red and green stripes beside it. He
   was shown it rendered during PD-3, beside those stripes, and kept it:
   it was already the house answer in four places before either round.

   FILES: ten templates.                           [test_warn_stripe.py]
"""
import os
import re
import sys

import alv_tree as T

SUFFIX = '.bak_warnstripe'
TOKEN = 'var(--alv-warn)'

# A LEFT BORDER PAINTED #ffc107, in either of the two forms it is
# written in. Nothing else: `border: 1px solid #ffc107` paints all four
# sides and is a different component.
STRIPE = re.compile(r'(border-left(?:-color)?\s*:\s*[^;]*?)#ffc107\b',
                    re.I)

EXPECT = 11          # 8 shorthand + 3 longhand, measured before writing


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


def style_spans(text):
    """(start, end) of each <style> block's CONTENT.

    The substitution is confined to stylesheets on purpose. Fourteen of
    this colour's uses are outside one - in inline style= attributes and
    in script - and a var() is not always valid where they sit."""
    return [(m.start(1), m.end(1)) for m in
            re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I)]


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    done = 0
    pages = 0
    for p in T.templates():
        text = read(p)
        if '#ffc107' not in text.lower():
            continue
        out = []
        last = 0
        here = 0
        for a, b in style_spans(text):
            block, n = STRIPE.subn(lambda m: m.group(1) + TOKEN, text[a:b])
            if not n:
                continue
            out.append(text[last:a])
            out.append(block)
            last = b
            here += n
        if not here:
            continue
        out.append(text[last:])
        new = ''.join(out)
        if not check:
            backup(p)
            write(p, new)
        done += here
        pages += 1

    print('WS-1  stripes on the token : %d' % done)
    print('WS-1  pages touched        : %d' % pages)

    if check:
        if done:
            print('WS-1  NOT APPLIED')
            return 1
        print('WS-1  applied')
        return 0

    # ALL OR NOTHING. A round that converts seven of eleven leaves the
    # tree in a state nobody chose, and the next census reports a smaller
    # number that looks like progress.
    if done not in (0, EXPECT):
        print('WS-1  REFUSED: expected %d declarations, found %d'
              % (EXPECT, done))
        return 2
    print('WS-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
