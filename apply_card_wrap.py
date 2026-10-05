"""CW-1 - A CARD CELL THAT CANNOT WRAP PUSHES THE PAGE SIDEWAYS.

   Found while rendering RA-3, not reported: the Ingredient Shopping
   Units page overflows at every phone width. Measured before anything
   was changed:

       320px   scrollWidth 448   over +128
       390px   scrollWidth 448   over  +58
       414px   scrollWidth 448   over  +34
       768px   scrollWidth 768   over   +0

   WHAT STICKS OUT is the Conversion cell's badges - `Missing` and `N/A`
   sitting at 384..448 on a 390px screen, outside their own <td>, which
   ends at 353.

   THE CAUSE IS IN BASE, NOT ON THE PAGE. base's card pattern turns every
   table row into a stacked card and lays each cell out as a flex row,
   label on the left and value on the right:

       .alv-table td         { display: flex; justify-content: space-between;
                               align-items: center; gap: 8px;
                               min-height: 28px; }
       .alv-table td::before { content: attr(data-label); flex-shrink: 0; }

   Flex does not wrap unless it is told to, and the label is explicitly
   `flex-shrink: 0`. So a cell whose VALUE is wider than the room the
   label leaves has nowhere to go and leaves the page. That is true of
   every card table in the app; Ingredients is simply the first one with
   a value wide enough to prove it.

   ONE DECLARATION. `flex-wrap: wrap` on that rule. The value drops to
   its own line when it does not fit and stays beside the label when it
   does.

   WHAT IT COSTS, painted across eight card tables at 390px:

       ingredient_base_units   over +58 -> +0     card height 251 -> 287
       property_detail         over  +0 -> +0     card height 1120 -> 1128
       tenant                  over  +0 -> +0     281 -> 281
       properties              over  +0 -> +0     245 -> 245
       measurement_units       over  +0 -> +0     319 -> 319
       physical_invoice_list   over  +0 -> +0     613 -> 613
       passport_management     over  +0 -> +0     455 -> 455

   Six of the eight do not move at all - nothing wraps that was not
   already fitting. The two that do are the two with a value too wide for
   its row, and they grow by exactly the height of the line it moves to.

   WHY IN BASE RATHER THAN ON THE PAGE. A page-local fix would have taken
   Ingredients off the overflow and left the next wide value - on any of
   the other hundred-odd card tables - free to do the same thing. The
   defect is the pattern, so the repair goes where the pattern lives.

   FILES: base.html.                               [test_card_wrap.py]
"""
import os
import re
import sys

import alv_tree as T

SUFFIX = '.bak_cardwrap'

# base writes this block one declaration per line, so the anchor is
# written the same way. A normalised-whitespace anchor matched nothing and
# the round refused rather than guessing - which is the gate doing its job.
OLD = """          display: flex;
          justify-content: space-between;"""
NEW = """          display: flex;
          /* CW-1, 5 Oct 2026 - or the value leaves the page.
             The label beside it is flex-shrink: 0, so a value wider than
             the room it leaves had nowhere to go: the Ingredients
             Conversion cell put its badges 58px past a 390px screen.
             Six of the eight card tables painted do not move at all. */
          flex-wrap: wrap;
          justify-content: space-between;"""


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


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    path = T.path_of('base.html')
    text = read(path)

    if 'flex-wrap: wrap;\n          justify-content' in text:
        print('CW-1  card cells wrapped : 0')
        if check:
            print('CW-1  applied')
            return 0
        print('CW-1  ok')
        return 0

    # MATCHED ONCE. base carries `display: flex` scores of times, and a
    # round that adds flex-wrap to the wrong one is a round nobody asked
    # for - so the anchor is the PAIR of lines, display then
    # justify-content, which occurs exactly once.
    n = text.count(OLD)
    if n != 1:
        raise SystemExit('CW-1: the card cell rule matched %d times, '
                         'expected 1' % n)

    text = text.replace(OLD, NEW, 1)
    if not check:
        backup(path)
        write(path, text)

    print('CW-1  card cells wrapped : 1')
    if check:
        print('CW-1  NOT APPLIED')
        return 1
    print('CW-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
