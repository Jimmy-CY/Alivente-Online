"""LA-1 - A SENTENCE THAT POINTED THE WRONG WAY.

   Demetri, 5 Oct 2026: "The Generate Lease Agreement function and Button
   works perfectly and generates the lease agreement pdf. Step 3 needs to
   say 'click the button above ....' - since we moved the buttons to the
   top."

   generate_lease_agreement.html, step 3:

       Review your selections and click the button below to generate the
       lease agreement.

   The button has not been below it since the action bar moved to the top
   of every screen. One word.

   A ONE-STRING ROUND STILL GETS A SUITE, and the suite is worth more
   than the change. Section 2 censuses the whole tree for prose pointing
   at a control by DIRECTION - "below", "above", "on the right" - and
   prints what it finds, because a sentence that tells someone where to
   look is a sentence that goes stale the moment a layout moves, and
   nothing in this repo was watching for them. This one was the only
   "button below" in 150 templates; the census is what will catch the
   next one.

   FILES: generate_lease_agreement.html.         [test_lease_above.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_leaseabove'

OLD = ('<p class="mb-3">Review your selections and click the button below '
       'to generate the lease agreement.</p>')
NEW = ('<p class="mb-3">Review your selections and click the button above '
       'to generate the lease agreement.</p>')


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

    path = T.path_of('generate_lease_agreement.html')
    text = read(path)

    if NEW in text:
        print('LA-1  edits : 0')
        print('LA-1  applied' if check else 'LA-1  ok')
        return 0

    n = text.count(OLD)
    if n != 1:
        raise SystemExit('LA-1: the step 3 sentence matched %d times, '
                         'expected 1' % n)
    text = text.replace(OLD, NEW, 1)
    if not check:
        backup(path)
        write(path, text)

    print('LA-1  edits : 1')
    if check:
        print('LA-1  NOT APPLIED')
        return 1
    print('LA-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
