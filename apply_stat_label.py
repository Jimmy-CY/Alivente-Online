"""SL-1 - A STAT LABEL MUST NOT CROSS ITS OWN TILE.

   Demetri, 4 Oct 2026, on the Projects task list in Greek:

       "The Completed Box Cuts off in Greek."

   THE MEASUREMENT. `.alv-stat-label` is a base component: uppercase,
   0.78rem, 0.4px of letter-spacing. English labels are short and the tile
   never had to cope. Greek ones are not: COMPLETED is nine characters,
   ΟΛΟΚΛΗΡΩΜΕΝΕΣ is thirteen, and uppercase Greek is wider per character
   than uppercase English.

   Three tiles in a col-md-4 are 109px each. Rendered at 1200, the middle
   label measured 44px WIDER THAN ITS TILE. It is one word with no space in
   it, so it could not wrap, and `.alv-stat` sets no overflow - so it simply
   drew across the border and over its neighbour. That is the cut-off.

   WHY THE PHONE WAS ALREADY BETTER. base's 3-up phone rule has carried
   `overflow-wrap: break-word` since the 3-up round. Below 768px the word
   breaks and stays inside the tile. The defect only ever existed at the
   widths where that rule does not apply - which is why it took a Greek
   task list on a laptop to find it.

   THE FIX is the same declaration, on the component itself rather than on
   one of its variants, so every tile in the tree is covered at every width.
   The 3-up rule's copy then has nothing left to say and goes.

   WHAT THIS ROUND DELIBERATELY DOES NOT DO. Breaking inside a word can
   leave a single character on the second line - on a 360px phone the Greek
   for Completed breaks as ΟΛΟΚΛΗΡΩΜΕΝΕ / Σ. `text-wrap: balance` does not
   help: it balances between words and this break is inside one. The lever
   that does fix it is dropping `text-transform: uppercase`, which makes
   Greek about a fifth narrower - and changes the house voice on every stat
   label in the app. Rendered, put to Demetri, and held back deliberately:

       "Break the word (Recommended)"   - 4 Oct 2026

   The orphan is tidy enough. The overflow was not.

   FILES: base.html.                            [test_stat_label.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_statlabel'

# The component rule, as it stands. Matched whole so a changed neighbour
# cannot be patched by accident.
OLD_LABEL = """      .alv-stat-label {
        font-size: 0.78rem;
        color: var(--alv-ink-soft);
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-top: 4px;
      }"""

NEW_LABEL = """      .alv-stat-label {
        font-size: 0.78rem;
        color: var(--alv-ink-soft);
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-top: 4px;
        /* SL-1, 4 Oct 2026. A label is one word often enough - Completed,
           Pending, Overdue - and in Greek one word is thirteen characters
           of uppercase. With nothing to break on it drew 44px past its own
           tile at 1200 and over the tile beside it. Demetri: "The
           Completed Box Cuts off in Greek."

           On the component, not on .is-3up where this used to live, so
           every tile is covered at every width and not only below 768. */
        overflow-wrap: break-word;
      }"""

# The 3-up variant's copy, now redundant. Removed rather than left to rot:
# two places declaring the same thing is how a rule ends up changed in one
# of them.
OLD_3UP = """        .alv-stats.is-3up .alv-stat-label { font-size: 0.66rem;
                                            letter-spacing: .2px;
                                            overflow-wrap: break-word; }"""

NEW_3UP = """        .alv-stats.is-3up .alv-stat-label { font-size: 0.66rem;
                                            letter-spacing: .2px; }"""

EDITS = [
    ('base.html', OLD_LABEL, NEW_LABEL),
    ('base.html', OLD_3UP, NEW_3UP),
]


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


def page(name):
    hits = [p for p in T.templates() if T.rel(p) == name]
    if len(hits) != 1:
        raise SystemExit('SL-1: %s matched %d templates' % (name, len(hits)))
    return hits[0]


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    done = 0
    for name, old, new in EDITS:
        path = page(name)
        text = read(path)
        if new in text:
            continue                       # already applied
        n = text.count(old)
        if n != 1:
            raise SystemExit('SL-1: %s contains the anchor %d times, '
                             'expected 1 - refusing' % (name, n))
        if not check:
            backup(path)
            write(path, text.replace(old, new))
        done += 1

    print('SL-1  edits applied : %d' % done)
    if check:
        if done:
            print('SL-1  NOT APPLIED')
            return 1
        print('SL-1  applied')
        return 0
    if done not in (0, len(EDITS)):
        print('SL-1  REFUSED: %d of %d edits' % (done, len(EDITS)))
        return 2
    print('SL-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
